---
name: todo-add
description: >
  Captures a new Todoist task from natural conversation: title, description,
  priority, due date, project/section, and labels inferred from context and
  the user's existing Todoist structure. Triggers include "add this to
  Todoist", "make a task for this", "remind me to", "작업 등록", "Todoist에
  추가해줘", "할 일로 남겨줘".
metadata:
  version: "1.0"
---

# todo-add

Capture a Todoist task from natural conversation. Detect the intent from
meaning, not trigger phrases, and do not require a fixed command format.

## Todoist connection

Use the `backend` setting when present; otherwise use Todoist MCP if
available, then the authenticated `td` CLI. If neither is available, tell
the user to connect Todoist MCP or install `td` (`npm install -g
@doist/todoist-cli`, Node 24+) and run `td auth login`. Jev is optional;
without it, choose the project and labels yourself.

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
exists, read it; if it names a `guide` file, read that too. The user's
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
- **Labels**: with `[labels.allowed]` / `[labels.projects]` set, use only
  those, by their meanings:
  1. `required_prefix` set → exactly one label with that prefix, naming
     the task's main action (not needed on a header that only groups
     subtasks).
  2. A `[labels.projects]` label only when that project is explicitly named.
  3. Other allowed labels only when they will help find the task later.
  Never use a label listed in `[labels.retired]`. Without an allowlist,
  choose among existing labels the same way.

### Jev suggestions (only when `[jev] enabled = true`)

Before choosing project and labels yourself, pipe `{"title",
"description", "parent_title"?, "projects": [{"id", "name", "parent"?,
"description"?, "inbox"?}]}` into `python3 scripts/jev_place.py`
(Windows: `py -3`), run from this skill's own directory. It returns a
project, an action label, a project label, and other labels from the
settings, with probabilities.

- Adopt `project_label` and `extra_labels` with `p >= 0.5`, and `project`
  with `confidence >= 0.7`; below that, choose yourself.
- Treat `act` as a hint only and choose the action label yourself.
- Values the user stated always win.

These thresholds were measured on the author's tasks; they are defaults.
Exit 2 (key missing), 3 (not enabled), or any failure: place the task
yourself without mentioning Jev unless asked.

### Grouping (only when `[grouping] header_prefix` is set)

- In the chosen project, look for a header task (title starting with the
  prefix) or open tasks sharing the new task's goal, source, or repository.
- A matching header exists → add the task under it.
- Two or more tasks from one request, or one related task already loose →
  first add the header (non-completable, no action label), then add the
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
