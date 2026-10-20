# todoist-skills

Agent skills for managing Todoist from a conversation: add, edit, find,
complete, audit, tidy, and reconcile tasks. Each skill is a self-contained folder under
`skills/`; install all of them or only the ones you want.

| Skill | Does | Changes tasks |
|---|---|---|
| `todo-add` | Creates a task with title, description, priority, due date, project, and labels inferred from the conversation | yes |
| `todo-update` | Edits an existing task, including confirmed session changes to its plan; keeps recurrence when only the date changes | yes |
| `todo-find` | Lists tasks by date, project, label, text, or topic; answers what was completed | no |
| `todo-complete` | Completes or reopens tasks; deletes only after confirmation | yes |
| `todo-tidy` | Checks section fit, shows a scoped organization plan, and applies clear edits | yes |
| `todo-doctor` | Audits tasks against your label and naming rules | no |
| `todo-reconcile` | Compares task plans with current project evidence; proposes relevant updates | only when requested |

## Choose the skill

Use `todo-find` to retrieve tasks, `todo-doctor` to diagnose hygiene, and `todo-tidy` to organize or apply a configured template while preserving intent.
Section-fit checks also use `todo-tidy`; check-only requests report suitable placements and proposed moves without writes.
Use `todo-update` for specified edits or confirmed session changes, and `todo-reconcile` to investigate whether a task matches current project decisions and implementation.
Reconciliation is read-only unless updates are requested; it preserves formatting unless template application is also requested.
A request to fix audit findings is an edit/organization request, not an audit write or another blanket approval gate.
Use `todo-add` for new tasks and `todo-complete` for completion, reopening or confirmed deletion.
Each skill works alone; references to another skill identify a responsibility, not a required sibling installation.
Reconciliation also needs access to relevant project sources; missing sources limit the result rather than imply no changes.

## Requirements

Every skill needs **one** way to reach Todoist. Nothing else is required.

| Option | Setup |
|---|---|
| Todoist MCP server | Connect Todoist in your agent (e.g. the Todoist connector in Claude) |
| `td`, the official [Todoist CLI](https://github.com/Doist/todoist-cli) | `npm install -g @doist/todoist-cli` (Node 24+), then `td auth login` |

Neither option is preferred. Name the one you want in a request, or set
`backend = "mcp"` or `backend = "td"` in the settings. With neither, the skills
use the one your session has. When both are there, the skills ask once per
request; the answer applies to that request only and is never saved.

First-time setup: copy `config.example.toml` to your settings path, uncomment
the `backend` line for the option you chose, and keep it. If you skip this,
the rule above applies.

Optional, per skill:

| Skill | Optional extra | Needs |
|---|---|---|
| `todo-add`, `todo-update` | Jev project and label suggestions | Python 3.11+, `TYPESAFE_API_KEY` |
| `todo-find` | Jev topic search (finds tasks that never name the topic) | Python 3.11+, `TYPESAFE_API_KEY`, `TODOIST_API_TOKEN` |
| `todo-doctor` | Jev fast audit (the task list stays out of the conversation) | Python 3.11+, `TYPESAFE_API_KEY`, `TODOIST_API_TOKEN` |
| `todo-complete` | — | — |

Without an optional extra, the skill does the same job itself.

## Install

Clone the repository and link the skills you want into your agent's skill
folder, so `git pull` updates them:

```bash
git clone https://github.com/korenl137/todoist-skills.git ~/src/todoist-skills
for s in ~/src/todoist-skills/skills/*/; do
  ln -s "$s" ~/.claude/skills/     # Claude Code
  ln -s "$s" ~/.agents/skills/     # Codex
done
```

Each folder under `skills/` also works on its own: link or copy only the
ones you need.

## Your settings (optional)

Without settings, the skills follow the projects and labels your Todoist
already has. To give them your own rules, copy
[`config.example.toml`](config.example.toml) to
`~/.config/todoist-skills/config.toml` (or set `TODOIST_SKILLS_CONFIG`) and
edit it:

| Setting | Effect |
|---|---|
| `[labels.allowed]`, `[labels.projects]` | The only labels tasks may carry, with their meanings |
| `labels.selection` | `multiple`: optional independent labels, including multiple actions/goals. Omitted or `legacy`: previous prefix-based contract |
| `[labels.roles]` | Optional role metadata for defined names: action, project, topic, state; no required counts |
| `labels.required_prefix` | Legacy mode only: one action with this prefix on an executable task. Ignored in multiple mode |
| `labels.ignore`, `[labels.retired]` | Labels never flagged; old labels and their replacements |
| `[areas]` | Top-level projects that split your tasks (e.g. Personal, Work) |
| `grouping.header_prefix` | Group related tasks under a header task |
| `guide` | Written task conventions; relative paths resolve from the config directory, ~ expands to the local home |
| `backend` | The Todoist route, `mcp` or `td`; unset means the route your session has, asking when both exist |
| `[jev]` | Turn on the optional Jev features and choose whether descriptions are sent |

In multiple mode, add a label only when it supports a useful retrieval and the
context supports its meaning. A task may have no labels, or several topics,
goals and actions; do not fill one slot of every role. State labels need a
confirmed condition and its release criteria, not a date-based guess.
Keep stored classification separate from inferred retrieval. Union counts deduplicate
task IDs; overlapping label counts do not add up to a total. Completion events
need their occurrence identity/time, particularly for recurrence. Vault note tags
remain independent of task labels and historical snapshots are not rewritten.

Role definitions must refer to allowed/project labels. Invalid settings stop
optional scripts with exit 4 and a diagnostic; do not silently use another taxonomy.
Legacy configs and legacy placement output keep their previous behavior.
Multiple-mode placement returns independent `labels` hints with name, probability
and role instead of the single `act`/`project_label` fields. Hints do not authorize
writes and state/action labels need context review; the model is optional.

What you say in a request always overrides the settings. All skills read
the same file, so each rule is written once.

### Task template guide (optional)

[`docs/task-template-guide.md`](docs/task-template-guide.md) is a ready-made
written convention (in Korean) you can point `guide` at: one core task
template (title, description blocks, status values, dates, priority) plus
per-type variants, with rules for adding and updating tasks. `todo-complete` reads the
guide's `## 완료 기준` before completing; it adds evidence comments only when you ask.
Copy it, edit it to taste, and set
`guide = "task-template-guide.md"`. It adds no settings and no labels of its
own; labels still come from your `[labels.*]` definitions, and where the guide
and your settings disagree, the skills report it. Missing optional example
labels are not disagreements.

Preserve an existing personal guide instead of silently replacing it. If AEM
or another manager owns your links or config directory, keep those paths intact;
test with a separate config selected by `TODOIST_SKILLS_CONFIG`. Existing
skills need no relinking for this documentation-only change. See the
[local validation scenarios](dev/task-template-guide-scenarios.md).

## Jev (optional)

[TypeSafe Jev](https://typesafe.ai) gives the scripts calibrated judgments
(which project fits, which tasks relate to a topic, which titles are vague).
To use it:

1. Set `[jev] enabled = true` in your settings.
2. Put `TYPESAFE_API_KEY=…` in the environment or `~/.config/typesafe/.env`.
3. For `todo-find` and `todo-doctor`, also `TODOIST_API_TOKEN=…` (Todoist →
   Settings → Integrations → Developer) in the environment or
   `~/.config/todoist/.env`. Logging in to `td` does not provide this token.

To turn Jev off, set `enabled = false` in the settings file, or point
`TODOIST_SKILLS_CONFIG` at a copy with it off for one session. The scripts
then exit with code 3, and the skills work without Jev.

The Jev fast paths in `todo-find` and `todo-doctor` read tasks through the
Todoist API with `TODOIST_API_TOKEN`, whichever route (MCP or `td`) you chose.

What leaves your machine: task titles, parent task titles, project and label
names, and your label meanings. Descriptions are sent only with
`send_descriptions = true`.

## Development

Each skill that uses Jev carries its own copy of `jevlib.py` (and
`todo-update` a copy of `jev_place.py`) so every folder stands alone. Edit
`dev/jevlib.py` or `skills/todo-add/scripts/jev_place.py`, then run:

```bash
python3 dev/sync.py
python3 -m unittest discover -s tests
```

The tests fail when a copy is out of date.

Check the `td` examples in each `SKILL.md` against the installed CLI without
accessing Todoist:

```bash
python3 dev/check_td_commands.py
```

For role boundaries and failure handling, review the per-skill `evals/scenarios.json` and
[`dev/role-boundary-scenarios.md`](dev/role-boundary-scenarios.md). These are decision scenarios, not executed model evals.

For session-based plan edits, review the manual decision cases in
[`dev/todo-update-scenarios.md`](dev/todo-update-scenarios.md).

The optional live check uses `TODOIST_API_TOKEN` (or
`~/.config/todoist/.env`), reads Todoist, creates one `[td-test]` task in
Inbox, checks update/reschedule/move behavior, and deletes the task even if a
check fails:

```bash
python3 dev/check_td_commands.py --live
```

The script uses `td` with Node 24+; otherwise it runs
`npx -y @doist/todoist-cli@5.5.2`. The checker prints the selected executable and
version; an installed `td` remains usable and its version is reported.
Update the fallback pin explicitly after rerunning the command checks; do not
resolve a new package version during each test. Keep this network/account check separate from
the default unit tests.

## License

[MIT](LICENSE).
