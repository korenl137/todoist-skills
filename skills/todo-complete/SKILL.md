---
name: todo-complete
description: >
  Marks Todoist tasks done or reopens them, and deletes tasks after
  confirmation. Triggers include "mark this done", "I finished this",
  "reopen it", "delete this task", "이거 완료 처리해줘", "완료 취소해줘",
  "이 작업 삭제해줘".
metadata:
  version: "1.0"
---

# todo-complete

Complete, reopen, or delete Todoist tasks.

## Tools

| Need | Required | Options | Without it |
|---|---|---|---|
| Todoist access | yes | Todoist MCP, or the `td` CLI (below) | stop and tell the user how to set one up |

For Todoist access, either of these; nothing else is required.

- **Todoist MCP** (tools such as `find-tasks`, `complete-tasks`), or
- **`td`**, the official Todoist CLI: `npm install -g @doist/todoist-cli`
  (Node 24+), then `td auth login`.

Use `backend` from `$TODOIST_SKILLS_CONFIG` or
`~/.config/todoist-skills/config.toml` if set; otherwise the MCP when its
tools are available, else `td` when `td auth status` succeeds. With
neither, stop and tell the user these two options.

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

Afterwards, briefly report what was done to which task.
