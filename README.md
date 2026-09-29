# todoist-skills

Agent skills for managing Todoist from a conversation: add, edit, find,
complete, and audit tasks. Each skill is a self-contained folder under
`skills/`; install all of them or only the ones you want.

| Skill | Does | Changes tasks |
|---|---|---|
| `todo-add` | Creates a task with title, description, priority, due date, project, and labels inferred from the conversation | yes |
| `todo-update` | Edits an existing task; keeps recurrence when only the date changes | yes |
| `todo-find` | Lists tasks by date, project, label, text, or topic; answers what was completed | no |
| `todo-complete` | Completes or reopens tasks; deletes only after confirmation | yes |
| `todo-doctor` | Audits tasks against your label and naming rules | no |

## Requirements

Every skill needs **one** way to reach Todoist. Nothing else is required.

| Option | Setup |
|---|---|
| Todoist MCP server | Connect Todoist in your agent (e.g. the Todoist connector in Claude) |
| `td`, the official [Todoist CLI](https://github.com/Doist/todoist-cli) | `npm install -g @doist/todoist-cli` (Node 24+), then `td auth login` |

The skills use the MCP when its tools are available, otherwise `td`. Set
`backend` in the settings to force one.

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
| `labels.required_prefix` | One label with this prefix on every task (e.g. an action label `kind/…`) |
| `labels.ignore`, `[labels.retired]` | Labels never flagged; old labels and their replacements |
| `[areas]` | Top-level projects that split your tasks (e.g. Personal, Work) |
| `grouping.header_prefix` | Group related tasks under a header task |
| `guide` | A file with your own written conventions, read before labeling and auditing |
| `[jev]` | Turn on the optional Jev features and choose whether descriptions are sent |

What you say in a request always overrides the settings. All skills read
the same file, so each rule is written once.

## Jev (optional)

[TypeSafe Jev](https://typesafe.ai) gives the scripts calibrated judgments
(which project fits, which tasks relate to a topic, which titles are vague).
To use it:

1. Set `[jev] enabled = true` in your settings.
2. Put `TYPESAFE_API_KEY=…` in the environment or `~/.config/typesafe/.env`.
3. For `todo-find` and `todo-doctor`, also `TODOIST_API_TOKEN=…` (Todoist →
   Settings → Integrations → Developer) in the environment or
   `~/.config/todoist/.env`. Logging in to `td` does not provide this token.

What leaves your machine: task titles, parent task titles, project and label
names, and your label meanings. Descriptions are sent only with
`send_descriptions = true`. The scripts exit with code 3 while Jev is off,
and the skills then work without it.

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

The optional live check uses `TODOIST_API_TOKEN` (or
`~/.config/todoist/.env`), reads Todoist, creates one `[td-test]` task in
Inbox, checks update/reschedule/move behavior, and deletes the task even if a
check fails:

```bash
python3 dev/check_td_commands.py --live
```

The script uses `td` with Node 24+; otherwise it runs
`npx -y @doist/todoist-cli`. Keep this network/account check separate from
the default unit tests.

## License

[MIT](LICENSE).
