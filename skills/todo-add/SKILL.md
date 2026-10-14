---
name: todo-add
description: >
  Captures a new Todoist task from natural conversation: title, description,
  priority, due date, project/section, and labels inferred from context and
  the user's existing Todoist structure. Triggers include "add this to
  Todoist", "make a task for this", "remind me to", "작업 등록", "Todoist에
  추가해줘", "할 일로 남겨줘".
metadata:
  version: "1.2"
---

# todo-add

## Contents

- Tools
- Todoist connection
- Settings (optional)
- Creating a task
- Explicit values vs inference
- Task quality
- Execution

Capture a Todoist task from natural conversation. Detect the intent from
meaning, not trigger phrases, and do not require a fixed command format.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Create tasks; read project, section and label names | One Todoist route: Todoist MCP or the `td` CLI, whichever the user names or `backend` sets | `backend` setting (`mcp` or `td`) to fix the route; Jev suggestions when `[jev] enabled = true` | Without Jev, choose project and labels yourself. If the chosen route is unavailable, say so, give its setup, then stop. |

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
| List projects / sections / labels | `find-projects` / `find-sections` / `find-labels` | `td project list --json` / `td section list "<project>" --json` / `td label list --json` |
| Tasks in a project | `find-tasks` with `projectId` | `td task list --project "<project>" --json` |
| Add a task | `add-tasks` | `td task add "<title>" --project … --section … --parent id:… --labels a,b --priority p2 --due "…" --json` (description via `--stdin`) |
| Add a header task | `add-tasks` with `isUncompletable: true` | `td task add "<title>" --uncompletable …` |
| Put an existing task under a header | `update-tasks` with `parentId` | `td task move id:<id> --parent id:<header>` |

Priorities are `p1` (highest) to `p4` on both.

## Settings (optional)

If `$TODOIST_SKILLS_CONFIG` or `~/.config/todoist-skills/config.toml`
exists, read it; if it names a `guide` file, read that too. Resolve relative
guide paths from the settings file's directory; expand ~ in absolute paths. The user's
words in the conversation always win. Without settings, follow the labels,
projects, and naming the user's Todoist already has.

## Creating a task

Determine from the conversation, not necessarily all stated explicitly:
a concise actionable title, useful context for the description, priority,
due date, project/section, and labels.

For requests that refer back to the discussion ("add this as a task"),
derive the actual task from that discussion instead of a vague one like
"check this". Put in the description only what helps when the task is
revisited, not the whole conversation.

### Project, section, labels

Look up what exists first and pick the closest existing fit; never create
new projects, sections, or labels to get an exact match.

- **Project/section**: the best-fitting existing one. With `[areas]` set,
  first pick the area (top-level project) whose description fits.
- **Labels**: use configured allowed/project meanings, or existing labels when
  no allowlist exists. Never add retired labels or invent a taxonomy.
  With `labels.selection = "multiple"`, zero or several labels are valid,
  including multiple actions and goals. Add each only for a useful retrieval
  supported by the task's purpose/context, not a product name in a source link.
  `[labels.roles]` describes roles without requiring a label from every role.
  Without selection, or with `legacy`, retain `required_prefix`: one main action
  when configured, except a header that only groups subtasks.
- Named goal labels need supporting task/parent context. Do not copy every
  parent's label to its children; a child's action/state needs its own evidence.
- State labels need a confirmed condition, with reason and release criteria in
  the description. No waiting label is not proof a task is executable. If
  prerequisites/access cannot be checked, report the uncertainty.

### Jev suggestions (only when `[jev] enabled = true`)

Before choosing project and labels yourself, pipe `{"title",
"description", "parent_title"?, "projects": [{"id", "name", "parent"?,
"description"?, "inbox"?}]}` into `python3 scripts/jev_place.py`
(Windows: `py -3`), run from this skill's own directory. It returns a
project and label hints with probabilities. Multiple mode returns a `labels`
list (label, p, role); legacy mode retains act/project_label/extra_labels.

- In legacy mode, consider `project_label` and `extra_labels` with `p >= 0.5`, and `project`
  with `confidence >= 0.7`; below that, choose yourself.
- In multiple mode, review each independent `labels` hint against its meaning
  and actual evidence; do not pick exactly one or require any. Action and state
  hints always need judgment; model probability alone does not establish a state.
- Treat legacy `act` as a hint only and choose the action label yourself.
- Values the user stated always win.

These thresholds were measured on the author's tasks; they are defaults.
Invalid settings (exit 4): report and stop classification until resolved; do not invent defaults.
Exit 2 (key missing), 3 (not enabled), or a model failure: place the task
yourself without mentioning Jev unless asked.

### Grouping (only when `[grouping] header_prefix` is set)

- In the chosen project, look for a header task (title starting with the
  prefix) or open tasks sharing the new task's goal, source, or repository.
- A matching header exists → add the task under it.
- Two or more tasks from one request, or one related task already loose →
  first add the header (non-completable, no required action label), then add the
  tasks under it and move the loose one there.
- Otherwise add it at the project level.

## Explicit values vs inference

Always keep what the user specified. For the rest:

- Project/section and labels: infer as above.
- Priority: the user's usual default.
- Due date: leave unset unless stated or clearly implied.

Do not ask merely because something was omitted. Ask only when ambiguity
would change what the task means, an important deadline, or a destination
whose alternatives mean substantially different things.

## Task quality

Titles are concise actions in the user's language, e.g. `Document the fix
for the server shutdown bug`, not `Server` or `Check this`. The description
holds supporting details, constraints, references, or why the task exists.
Point to the source document instead of copying state that changes; if
state must be written, date it. When the task waits on another, name that
task.

## Execution

Creating a task is low-risk and reversible: once the intent is clear, add
it without asking, then briefly report what was created and where.
