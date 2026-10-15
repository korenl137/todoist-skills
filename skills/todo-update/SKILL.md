---
name: todo-update
description: >
  Edits an existing Todoist task's title, description, priority, due date,
  deadline, project/section, or labels from natural conversation, including
  reflecting confirmed session progress and plan changes. Triggers
  include "change this task's priority", "push the due date to next week",
  "add a label", "move this task", "우선순위 P1로 바꿔줘", "마감일 다음 주로
  옮겨줘", "라벨 추가해줘", "이번 세션 변경사항을 기존 계획에 반영해줘".
  Independent project freshness checks belong to todo-reconcile; organization belongs to todo-tidy.
metadata:
  version: "1.4"
---

# todo-update

## Contents

- Tools
- Todoist connection
- Settings (optional)
- Resolving the target task
- Applying the change
- Reflecting session changes in an existing plan
- Progress updates that are really completion
- Read coverage and dates
- Execution

Modify an existing Todoist task.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Read a task; change only the fields the user named | One Todoist route: Todoist MCP or the `td` CLI, whichever the user names or `backend` sets | `backend` setting (`mcp` or `td`) to fix the route; Jev placement suggestions when `[jev] enabled = true` | Without Jev, decide project and labels yourself. If the chosen route is unavailable, say so, give its setup, then stop. |

## Todoist connection

Use the route the user names in the request, for that request only. Otherwise
use `backend` from settings: `mcp` (Todoist MCP) or `td` (the td CLI). Neither
route is preferred. When `backend` is set, use that route without a question;
if it is unavailable, say so and give its setup, then stop; do not switch
routes silently. When `backend` is unset or holds any other value and only one
route is available, use it without a question. When both are available, ask
once, in the user's language: "Todoist 작업을 어떤 경로로 처리할까요? 1) Todoist MCP 커넥터 2)
td CLI". Apply the answer to this request only and write nothing to any file.
Then add one line: to stop this question, put `backend = "mcp"` or `backend =
"td"` in your settings file. If neither route is available, say how to connect
each one and stop. To connect Todoist MCP, connect Todoist in your agent. To
set up `td`, run `npm install -g @doist/todoist-cli` (Node 24+) and `td auth
login`. Jev is optional; without it, choose the project and labels yourself.

| Step | Todoist MCP | `td` |
|---|---|---|
| Find the task | `find-tasks` / `find-tasks-by-date` | `td task list --json` (with `--project`, `--label`, `--filter "<query>"`) / `td task view <ref> --json` |
| Change fields | `update-tasks` with only the changed fields | `td task update <ref> --content … --priority … --labels … --deadline … --json` |
| Change only the date | `reschedule-tasks` | `td task reschedule <ref> <date>` |
| Move | `update-tasks` with `projectId` / `sectionId` / `parentId` | `td task move <ref> --project … --section … --parent …` |
| Add a note | `add-comments` | `td comment add` (see `td comment --help`) |
| Complete | `complete-tasks` | `td task complete <ref>` |

Both backends have the same pitfalls:

- Setting labels **replaces** the whole list. To add one, read the current
  labels and send the union.
- Changing the due date through the due *string* (`dueString`, `--due`)
  can wipe a recurring task's repeat pattern. For a date-only change, use
  reschedule, which keeps it.
- Moving lifts a task out of its section or parent. Move only when the user
  wants the task relocated, never as a side effect of another edit.

## Settings (optional)

If `$TODOIST_SKILLS_CONFIG` or `~/.config/todoist-skills/config.toml`
exists, read it; if it names a `guide` file, read that too. Resolve relative
guide paths from the settings file's directory; expand ~ in absolute paths. The user's
words always win. Without settings, follow the labels and projects the
user's Todoist already has.

## Resolving the target task

The user rarely gives an ID.

- Reuse a task already surfaced in the conversation instead of searching
  again.
- Otherwise search by text, project, label, or date.
- One match → proceed. Several plausible matches that context does not
  settle → ask which one.
- No match → say so; do not create a task.

## Applying the change

- Re-read current fields before writing, especially after a delayed proposal; reconcile intervening edits rather than overwriting them.
- Send only the fields that change, following the pitfalls above.
- For explicitly requested reminder, duration or assignee changes, inspect the live schema or CLI help.
  Report unsupported fields; never silently substitute a scheduled date for a notification.
- When the user asks to relocate or relabel without naming the target
  ("move it where it belongs", "fix its labels"): choose from existing
  projects and labels, keeping to `[labels.allowed]` / `[labels.projects]`
  when set and never using `[labels.retired]`. Replace a retired label
  with its mapped replacements; when the mapping is empty, propose one. Keep
  labels the request does not concern, including those in `labels.ignore`.
- In multiple selection mode, zero or multiple labels are valid. Review useful
  purposes independently; do not replace one action just because another applies.
  Only legacy required_prefix imposes a main-action requirement.
- For requested progress/organization updates, reconcile relevant state labels
  against confirmed conditions and remaining dependencies. Preserve a state if
  evidence is missing or a blocking condition remains. Dates alone do not release
  waiting/on-hold, and no state label does not prove readiness.
- With `[jev] enabled = true`, you may get suggestions first: pipe
  `{"title", "description", "parent_title"?, "projects": [...]}` into
  `python3 scripts/jev_place.py` (Windows: `py -3`) from this skill's own
  directory. Adopt project labels and other labels with `p >= 0.5` and a
  project with `confidence >= 0.7`; treat the action label as a hint.
  In multiple mode, review each returned labels hint independently; never infer
  a confirmed action/state from probability alone. Exit 4 means invalid settings:
  report and stop relabeling rather than applying another scheme. On
  exit 2, 3, or a model failure, decide yourself without mentioning Jev.

## Reflecting session changes in an existing plan

Apply known, confirmed changes here; independent investigation of project freshness belongs to todo-reconcile.
When a template change is explicitly requested for a particular task, read its configured guide and preserve useful content while applying that format.
Organization or template normalization across a scope belongs to todo-tidy; a field-only edit does not authorize reformatting.

When asked to reflect session progress or an agreed plan change, read the
current task description and relevant child tasks. Apply only confirmed
progress and decisions from the conversation, not proposals or intended work.
Preserve the existing format and unrelated content: mark completed description
items, revise changed items, or update actual child tasks where the plan lives.
Complete only confirmed finished child tasks; partial progress does not
complete the parent. Do not add a session-summary comment unless requested.

## Progress updates that are really completion

If the user says the whole task is done ("update it, this is all finished"),
add the note as a comment (or in the description if that is where the
user keeps notes), then complete the task. Completion is reversible, so no
confirmation is needed. If the progress is partial, only edit.

## Read coverage and dates

Read every page needed for the requested scope, including child tasks, comments or completion events when relevant.
If a page or source is inaccessible, report partial coverage; do not present a partial count as an exact total or absence as proof.
Resolve relative dates and reporting periods using the user's stated timezone, otherwise the accessible account/session timezone.
For consequential ambiguity, ask; report the absolute date or period and timezone when it affects the result.
Distinguish a task's scheduled date from its deadline and an actual notification.

## Execution

Check each operation's result and read back changed fields and preserved metadata/hierarchy.
After a timeout, inspect current task state before retrying; for completion inspect occurrence history too.
Retry only unresolved safe operations; report partial success or an unknown outcome without repeating confirmed writes.

An edit is reversible, so apply it once the target and the change are
both clear. Ask only when several tasks could be the target, or the change
itself is ambiguous ("push it back" with no amount). Then briefly report
what changed on which task.
