---
name: todo-complete
description: >
  Marks Todoist tasks done or reopens them, and deletes tasks after
  confirmation. Triggers include "mark this done", "I finished this",
  "reopen it", "delete this task", "이거 완료 처리해줘", "완료 취소해줘",
  "이 작업 삭제해줘". Other field edits belong to todo-update.
metadata:
  version: "1.4"
---

# todo-complete

Complete, reopen, or delete Todoist tasks.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Complete, reopen or delete tasks | One Todoist route: Todoist MCP or the `td` CLI, whichever the user names or `backend` sets | `backend` setting (`mcp` or `td`) to fix the route | Delete only after the user confirms. If the chosen route is unavailable, say so, give its setup, then stop. |

## Todoist connection

Use the route the user names in the request, for that request only. Otherwise
use `backend` from `$TODOIST_SKILLS_CONFIG` or
`~/.config/todoist-skills/config.toml`: `mcp` (Todoist MCP) or `td` (the td
CLI). Neither route is preferred. When `backend` is set, use that route
without a question; if it is unavailable, say so and give its setup, then
stop; do not switch routes silently. When `backend` is unset or holds any
other value and only one route is available, use it without a question. When
both are available, ask once, in the user's language: "Todoist 작업을 어떤 경로로
처리할까요? 1) Todoist MCP 커넥터 2) td CLI". Apply the answer to this request only
and write nothing to any file. Then add one line: to stop this question, put
`backend = "mcp"` or `backend = "td"` in your settings file. If neither route
is available, say how to connect each one and stop. To connect Todoist MCP,
connect Todoist in your agent. To set up `td`, run `npm install -g
@doist/todoist-cli` (Node 24+) and `td auth login`.

| Step | Todoist MCP | `td` |
|---|---|---|
| Find the task | `find-tasks` / `find-tasks-by-date` | `td task list --json` / `td task view <ref> --json` |
| Complete / reopen | `complete-tasks` / `uncomplete-tasks` | `td task complete <ref>` / `td task uncomplete id:<id>` |
| Delete | `delete-object` (type `task`) | `td task delete <ref> --yes` |

Completing a recurring task advances it to the next date; stopping the
recurrence (`td task complete --forever`) needs the user to ask for it.

## Read coverage and dates

Read every page needed for the requested scope, including child tasks, comments or completion events when relevant.
If a page or source is inaccessible, report partial coverage; do not present a partial count as an exact total or absence as proof.
Resolve relative dates and reporting periods using the user's stated timezone, otherwise the accessible account/session timezone.
For consequential ambiguity, ask; report the absolute date or period and timezone when it affects the result.
Distinguish a task's scheduled date from its deadline and an actual notification.

## Resolving the target task

Reuse a task already surfaced in the conversation, or search for it. One
match → proceed. Several plausible matches → ask, especially before a
delete.

## Completing / reopening

Reversible, so do it once the target is clear and any completion criterion is confirmed (below), without confirmation.

## Completion criteria (when a guide is set)

If the settings file names a `guide`, read it before completing. Resolve a relative path from the settings file's directory, and expand `~` in absolute paths. Without a guide, complete as before.

For a task whose description has a `## 완료 기준` block, re-read the block and complete only when the conversation or a readable source confirms every condition in it. Name the confirming source in your report. If a condition is unconfirmed, do not complete: name the condition and ask whether to set the task to `검증 대기`. Change the status only when the user says yes. Do not add a completion comment unless the user asks for one.

A recurring task: complete it and leave its description unchanged.

## Deleting

Destructive and not reliably reversible. Always confirm the specific task
before deleting, even when the target is unambiguous. Never delete as a
side effect of another request ("mark it done" completes, never deletes).

Before asking, count what the delete takes with the task: child tasks (open
and completed) and comments. With MCP, use `fetch-object` with
`includeChildren` and `find-comments`; with `td`, find them with the CLI's help
(`td task --help`, `td comment --help`). State the counts in the confirmation.
Child tasks and comments may go with the task, so do not assume they are kept.

## Verify the outcome

Read back task state and relevant completion events; for recurring tasks check the intended occurrence and next date.
An active recurring task may already have been completed and advanced: after a timeout, inspect occurrence history before any retry.
If the outcome cannot be established, report it and stop rather than advance recurrence twice.
For deletion, verify absence with a reliable lookup; an access error alone does not establish deletion.
Check per-item results and report partial failures without repeating successful operations.
Afterwards, briefly report what was done to which task.
