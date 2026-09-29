---
name: todo-update
description: >
  Edits an existing Todoist task's title, description, priority, due date,
  deadline, project/section, or labels from natural conversation. Triggers
  include "change this task's priority", "push the due date to next week",
  "add a label", "move this task", "우선순위 P1로 바꿔줘", "마감일 다음 주로
  옮겨줘", "라벨 추가해줘".
metadata:
  version: "1.0"
---

# todo-update

Modify an existing Todoist task.

## Tools

| Need | Required | Options | Without it |
|---|---|---|---|
| Todoist access | yes | Todoist MCP, or the `td` CLI (below) | stop and tell the user how to set one up |
| Jev suggestions | no | Python 3.11+, `TYPESAFE_API_KEY`, and `[jev] enabled = true` in the settings | choose the project and labels yourself |

For Todoist access, either of these; nothing else is required.

- **Todoist MCP** (tools such as `find-tasks`, `update-tasks`), or
- **`td`**, the official Todoist CLI: `npm install -g @doist/todoist-cli`
  (Node 24+), then `td auth login`.

Use `backend` from the settings file if set; otherwise the MCP when its
tools are available, else `td` when `td auth status` succeeds. With
neither, stop and tell the user these two options.

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
exists, read it; if it names a `guide` file, read that too. The user's
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

- Send only the fields that change, following the pitfalls above.
- When the user asks to relocate or relabel without naming the target
  ("move it where it belongs", "fix its labels"): choose from existing
  projects and labels, keeping to `[labels.allowed]` / `[labels.projects]`
  when set and never using `[labels.retired]`. Replace a retired label
  with its mapped replacements; when the mapping is empty, propose one. Keep
  labels the request does not concern, including those in `labels.ignore`.
- With `[jev] enabled = true`, you may get suggestions first: pipe
  `{"title", "description", "parent_title"?, "projects": [...]}` into
  `python3 scripts/jev_place.py` (Windows: `py -3`) from this skill's own
  directory. Adopt project labels and other labels with `p >= 0.5` and a
  project with `confidence >= 0.7`; treat the action label as a hint. On
  exit 2, 3, or any failure, decide yourself without mentioning Jev.

## Progress updates that are really completion

If an "update" says the task is done ("update it, this is all finished"),
add the note as a comment (or in the description if that is where the
user keeps notes), then complete the task. Completion is reversible, so no
confirmation is needed. If the progress is partial, only edit.

## Execution

An edit is reversible, so apply it once the target and the change are
both clear. Ask only when several tasks could be the target, or the change
itself is ambiguous ("push it back" with no amount). Then briefly report
what changed on which task.
