# Sudo Helper Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Single-file pi extension that lets the LLM run `sudo` commands without a TTY.

**Architecture:** Intercepts `tool_call` for `bash` commands containing `sudo`, prompts user for password once via `ctx.ui.input`, primes the sudo ticket with `sudo -S -v`, then forwards the command as-is. A background 4-minute `setInterval` keeps the ticket alive. Password is nulled after `sudo -v` succeeds. Also registers a dedicated `sudo` custom tool.

**Tech Stack:** TypeScript, pi ExtensionAPI, no external dependencies.

---

### Task 1: Create the full extension

**Files:**
- Create: `~/.pi/agent/extensions/sudo-helper.ts`

- [ ] **Step 1: Write the extension file**

Write `~/.pi/agent/extensions/sudo-helper.ts`:

```typescript
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execSync } from "node:child_process";

// ── State ──────────────────────────────────────────────────────
let password: string | null = null;
let sudoTicketPrimed = false;
let failedAttempts = 0;
let blocked = false;
let timerId: ReturnType<typeof setInterval> | null = null;
let timerRunning = false;
const MAX_ATTEMPTS = 3;
const TICKET_REFRESH_MS = 4 * 60 * 1000; // 4 minutes

// ── Helpers ────────────────────────────────────────────────────

/**
 * Attempt to validate the password via sudo -v.
 * Returns true if the ticket was primed, false otherwise.
 */
function sudoValidate(pwd: string): boolean {
  try {
    execSync(`echo "${pwd}" | sudo -S -v`, {
      stdio: "pipe",
      timeout: 10_000,
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Extend the sudo ticket in the background.
 * Called by setInterval — no password needed, must have valid ticket.
 */
function sudoRefresh(): boolean {
  try {
    execSync("sudo -v", { stdio: "pipe", timeout: 10_000 });
    return true;
  } catch {
    return false;
  }
}

function startTimer(ctx: ExtensionContext) {
  if (timerRunning) return;
  timerRunning = true;
  timerId = setInterval(() => {
    if (!sudoRefresh()) {
      // Ticket expired (likely sleep/wake). Stop timer.
      stopTimer();
      sudoTicketPrimed = false;
      ctx.ui.notify("sudo ticket expired. Next sudo command will re-prompt.", "warning");
    }
  }, TICKET_REFRESH_MS);
}

function stopTimer() {
  if (timerId !== null) {
    clearInterval(timerId);
    timerId = null;
  }
  timerRunning = false;
}

function cleanup() {
  password = null;
  sudoTicketPrimed = false;
  failedAttempts = 0;
  blocked = false;
  stopTimer();
}

/**
 * Core logic: ensure the sudo ticket is primed.
 * If not primed, prompt user, validate, start timer.
 * Returns true if the caller should proceed, false to block.
 */
async function ensureSudoTicket(ctx: ExtensionContext): Promise<boolean> {
  if (blocked) {
    ctx.ui.notify("sudo blocked after 3 failed attempts. Restart pi to retry.", "error");
    return false;
  }

  if (sudoTicketPrimed) return true;

  if (!ctx.hasUI) {
    ctx.ui.notify("sudo needed but no UI available for password prompt.", "error");
    return false;
  }

  // Prompt for password
  const pwd = await ctx.ui.input({
    label: "🔒 Sudo password needed",
    password: true,
  });

  if (!pwd) {
    ctx.ui.notify("sudo command cancelled (no password provided).", "warning");
    return false;
  }

  // Validate via sudo -v
  if (!sudoValidate(pwd)) {
    failedAttempts++;
    if (failedAttempts >= MAX_ATTEMPTS) {
      blocked = true;
      ctx.ui.notify("sudo blocked after 3 failed password attempts. Restart pi to retry.", "error");
      return false;
    }
    ctx.ui.notify(
      `Wrong password (${failedAttempts}/${MAX_ATTEMPTS}). Try again.`,
      "warning",
    );
    return ensureSudoTicket(ctx);
  }

  // Success — null password immediately, start ticket timer
  password = null;
  sudoTicketPrimed = true;
  failedAttempts = 0;
  startTimer(ctx);
  ctx.ui.notify("sudo ticket primed. Valid for the duration of this session.", "info");
  return true;
}

// ── Extension ──────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
  // ── Transparent interception ────────────────────────────────
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return undefined;

    const command = (event.input as { command: string }).command;
    if (!command || !/\bsudo\b/.test(command)) return undefined;

    const ok = await ensureSudoTicket(ctx);
    if (!ok) {
      return { block: true, reason: "sudo not available" };
    }

    // Forward as-is — sudo ticket is valid
    return undefined;
  });

  // ── Dedicated sudo tool ─────────────────────────────────────
  pi.registerTool({
    name: "sudo",
    label: "Sudo",
    description:
      "Execute a command with superuser privileges. " +
      "Use this when you need to run apt, systemctl, or other commands that require root.",
    promptSnippet: "Run privileged commands via sudo's credential cache",
    promptGuidelines: [
      "Use the sudo tool (not bash with sudo prefix) when you need to run a single privileged command — this avoids ticket-prime overhead on bash interception.",
      "For multi-step privileged work, use the sudo tool for each privileged command rather than chaining them in one bash call.",
    ],
    parameters: Type.Object({
      command: Type.String({
        description: "The command to execute as root (without the 'sudo' prefix)",
      }),
    }),
    async execute(
      _toolCallId: string,
      params: { command: string },
      _signal: AbortSignal,
      _onUpdate: ((update: unknown) => void) | undefined,
      ctx: ExtensionContext,
    ) {
      const ok = await ensureSudoTicket(ctx);
      if (!ok) {
        return {
          content: [{ type: "text" as const, text: "sudo not available" }],
          isError: true,
        };
      }

      try {
        const result = execSync(params.command, {
          stdio: "pipe",
          timeout: 120_000,
          shell: "/bin/bash",
        });
        return {
          content: [
            {
              type: "text" as const,
              text: result.stdout?.toString() || "(no output)",
            },
          ],
          details: { exitCode: 0 },
        };
      } catch (err: unknown) {
        const error = err as {
          stdout?: Buffer;
          stderr?: Buffer;
          status?: number;
          message?: string;
        };
        const stdout = error.stdout?.toString() || "";
        const stderr = error.stderr?.toString() || "";
        const exitCode = error.status ?? 1;
        return {
          content: [
            {
              type: "text" as const,
              text: stderr || stdout || error.message || `Exit code ${exitCode}`,
            },
          ],
          isError: true,
          details: { exitCode },
        };
      }
    },
  });

  // ── Cleanup ─────────────────────────────────────────────────
  pi.on("session_shutdown", async (_event, _ctx) => {
    cleanup();
  });
}
```

- [ ] **Step 2: Reload pi extensions**

Run inside pi:

```
/reload
```

Expected: extension loads without errors. Startup should show the extension discovered.

- [ ] **Step 3: Test transparent interception**

Inside pi, run:

```
sudo echo "hello from sudo"
```

Expected: pi prompts for sudo password via masked input. After entering it, `echo "hello from sudo"` runs. Should see `hello from sudo`. No command rewriting needed — plain sudo works via the primed ticket.

- [ ] **Step 4: Test the dedicated sudo tool**

Trigger the tool via a prompt:

```
Run the command "echo hello-root" using the sudo tool
```

Expected: LLM calls the `sudo` tool, it prints `hello-root`.

- [ ] **Step 5: Test wrong password handling**

Start a fresh pi session (password cache is per-session). Trigger a sudo command, type wrong password 3 times.

Expected: After 3 failed attempts, the command is blocked with "sudo blocked" notification. Next attempt immediately blocked.

- [ ] **Step 6: Test timer keeps ticket alive**

Prime the sudo ticket. Wait 6 minutes (or set `TICKET_REFRESH_MS` to 10000 for testing). Run another sudo command.

Expected: ticket is still valid — sudo command runs without re-prompting.

- [ ] **Step 7: Commit**

```bash
cd /home/megamind/projects/hello-moto
git add ~/.pi/agent/extensions/sudo-helper.ts docs/superpowers/specs/2026-05-22-sudo-helper-design.md docs/superpowers/plans/2026-05-22-sudo-helper-plan.md
git commit -m "feat: add sudo-helper extension for privileged commands in pi"
```
