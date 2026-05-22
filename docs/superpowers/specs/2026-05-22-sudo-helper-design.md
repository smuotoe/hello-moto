# Sudo Helper Extension — Design Spec

**Date:** 2026-05-22
**Status:** Approved
**Extension:** `~/.pi/agent/extensions/sudo-helper.ts`

## Problem

Pi's `bash` tool runs shell commands without a TTY. `sudo` refuses to run without a TTY to prompt for a password, making it impossible for pi to perform privileged operations (apt install, systemctl, etc.) without the user manually typing the command in another terminal.

## Approach

A single-file pi extension (~100 lines) that:

1. Intercepts `bash` tool calls containing `sudo` commands
2. Prompts the user for their password once per pi session via pi's built-in masked input dialog
3. Uses `echo <password> | sudo -S -v` to validate and cache the password in `sudo`'s credential timestamp (default 5-minute window)
4. Nulls the password from memory immediately after `sudo -v` succeeds
5. Runs a `setInterval` every 4 minutes to silently extend the sudo ticket via `sudo -v`
6. Also registers a dedicated `sudo` tool the LLM can call explicitly

## Design Decisions (from grilling)

| Decision | Choice | Rationale |
|---|---|---|
| Password storage | Module variable, cleared after `sudo -v` | Minimizes in-memory exposure. Sudo ticket handles ongoing auth. |
| Re-prompt cadence | Once per session | Password survives only long enough for `sudo -v`. Timer keeps ticket alive. |
| Timer refresh | `setInterval` every 4 min | Keeps the sudo ticket alive indefinitely. No re-prompting needed during a session. |
| Wrong password | Re-prompt up to 3x, then block | Prevents lockout, gives room for typos, gives up on brute force. |
| Sleep/wake | Timer `sudo -v` fails → stop timer. Next `sudo` re-prompts | Rare edge case, simple handling. |
| Interaction model | Transparent interception + dedicated `sudo` tool | Both: LLM can write natural `sudo` commands or explicitly call the tool. |
| Command rewriting | None — uses `sudo -v` ticket | No fragile regex on command strings. Plain `sudo` calls just work. |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    sudo-helper.ts                           │
│                                                             │
│  state: {                                                    │
│    password: string | null     ← populated on prompt       │
│    sudoTicketPrimed: boolean   ← after successful -v       │
│    failedAttempts: number      ← wrong password counter    │
│    blocked: boolean            ← after 3 failed attempts   │
│    timerId: Timer | null       ← setInterval ref           │
│  }                                                          │
│                                                             │
│  Events:                                                    │
│    tool_call (bash) ──► detect sudo ──► prime ticket       │
│                                      ──► forward command   │
│                                                             │
│  Custom tool:                                               │
│    sudo(command) ──► same logic as intercept               │
│                                                             │
│  Timer:                                                     │
│    setInterval(4min) ──► sudo -v ──► extends ticket        │
│                                                             │
│  Cleanup:                                                   │
│    session_shutdown ──► clearInterval, null password       │
└─────────────────────────────────────────────────────────────┘
```

## Flow — First sudo command

```
1. LLM calls bash("sudo apt install ./foo.deb")
2. Extension detects \bsudo\b in command
3. Check: password cached? → No
4. Open ctx.ui.input({ password: true }) ──► user types password
5. Run: echo <password> | sudo -S -v
   ├── Success → null password, start 4-min interval
   └── Failure (wrong password) →
       ├── failedAttempts++
       ├── if < 3: re-prompt (step 4)
       └── if >= 3: set blocked=true, return { block: true, reason: "..." }
6. Forward original bash command (no rewriting — sudo ticket is valid)
7. Command succeeds
```

## Flow — Subsequent sudo commands

```
1. LLM calls bash("sudo systemctl restart reachy")
2. Extension detects sudo
3. Check: password cached? → Already nulled
4. Check: sudoTicketPrimed? → Yes
5. Forward original bash command as-is
6. sudo reads the valid ticket → no TTY prompt → succeeds
```

## Flow — Sleep/wake cycle

```
1. Machine sleeps for 2 hours
2. Timer fires on resume, runs sudo -v
3. sudo -v fails (ticket expired)
4. Extension clears sudoTicketPrimed flag, stops interval
5. Next sudo command: detects no valid ticket → prompts user → sudo -v → restart interval
```

## Dedicated `sudo` Tool

```typescript
pi.registerTool({
  name: "sudo",
  description: "Execute a command with superuser privileges.",
  parameters: {
    command: { type: "string", description: "Command to run as root" }
  },
  execute(params) {
    // Same ticket-prime-before-exec + ticket check as interceptor
  }
})
```

The tool exists alongside the transparent interceptor so the LLM has an explicit action when it knows elevated privileges are needed. This is especially useful when the LLM wants to compose multi-step privileged work.

## Implementation Plan

1. Create `~/.pi/agent/extensions/sudo-helper.ts`
2. Wire `tool_call` handler for `bash` with sudo detection
3. Wire `registerTool` for `sudo` custom tool
4. Wire `session_shutdown` for cleanup
5. Test with `sudo apt update` type command
6. Verify timer keeps ticket alive past 5 minutes

## Files

- **New:** `~/.pi/agent/extensions/sudo-helper.ts` (~100-120 lines)