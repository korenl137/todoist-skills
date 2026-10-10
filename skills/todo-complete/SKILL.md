---
name: todo-complete
description: >
  Marks Todoist tasks done or reopens them, and deletes tasks after
  confirmation. Triggers include "mark this done", "I finished this",
  "reopen it", "delete this task", "이거 완료 처리해줘", "완료 취소해줘",
  "이 작업 삭제해줘".
metadata:
  version: "1.2"
---

# todo-complete

Complete, reopen, or delete Todoist tasks.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Complete, reopen or delete tasks | One Todoist route: Todoist MCP or the `td` CLI, whichever the user names or `backend` sets | `backend` setting (`mcp` or `td`) to fix the route | Delete only after the user confirms. If the chosen route is unavailable, say so, give its setup, then stop. |

## Todoist connection

Use the route the user names in the request. Otherwise use `backend` from
`$TODOIST_SKILLS_CONFIG` or `~/.config/todoist-skills/config.toml`: `mcp`
(Todoist MCP) or `td` (the td CLI). Neither route is preferred. If `backend`
is unset or holds any other value, use the route this session has; when both
are available, ask once which to use. If the chosen route is unavailable, say
so and give its setup, then stop; do not switch routes silently. To connect
Todoist MCP, connect Todoist in your agent. To set up `td`, run `npm install
-g @doist/todoist-cli` (Node 24+) and `td auth login`.

| Step | Todoist MCP | `td` |
|---|---|---|
| Find the task | `find-tasks` / `find-tasks-by-date` | `td task list --json` / `td task view <ref> --json` |
| Complete / reopen | `complete-tasks` / `uncomplete-tasks` | `td task complete <ref>` / `td task uncomplete id:<id>` |
| Delete | `delete-object` (type `task`) | `td task delete <ref> --yes` |

Completing a recurring task advances it to the next date; stopping the
recurrence (`td task complete --forever`) needs the user to ask for it.

## Resolving the target task

Reuse a task already surfaced in the conversation, or search for it. One
match → proceed. Several plausible matches → ask, especially before a
delete.

## Completing / reopening

Reversible, so do it once the target is clear, without confirmation.

## Deleting

Destructive and not reliably reversible. Always confirm the specific task
before deleting, even when the target is unambiguous. Never delete as a
side effect of another request ("mark it done" completes, never deletes).

Before asking, count what the delete takes with the task: child tasks (open
and completed) and comments. With MCP, use `fetch-object` with
`includeChildren` and `find-comments`; with `td`, find them with the CLI's help
(`td task --help`, `td comment --help`). State the counts in the confirmation.
Child tasks and comments may go with the task, so do not assume they are kept.

Afterwards, briefly report what was done to which task.
