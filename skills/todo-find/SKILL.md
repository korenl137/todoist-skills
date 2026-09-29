---
name: todo-find
description: >
  Looks up and lists Todoist tasks by date range, project, label, search
  text, or topic; also answers what was completed. Read-only. Triggers
  include "what's on my list today", "show this week's tasks", "find tasks
  about X", "what did I finish", "오늘 할 일 뭐 있어", "이번 주 작업 목록
  보여줘", "완료한 작업 보여줘".
metadata:
  version: "1.0"
---

# todo-find

Look up Todoist tasks. Read-only: never changes anything, so no
confirmation is needed.

## Todoist connection

Use the `backend` setting when present; otherwise use Todoist MCP if
available, then the authenticated `td` CLI (read-only login is enough).
If neither is available, tell the user to connect Todoist MCP or install
`td` (`npm install -g @doist/todoist-cli`, Node 24+) and run `td auth login`.
Jev topic search is optional.

| Question | Todoist MCP | `td` |
|---|---|---|
| By date ("today", "this week") | `find-tasks-by-date` | `td today` / `td upcoming <days>` (`--json`) |
| By text, project, section, label, filter | `find-tasks` | `td task list --json` with `--project`, `--label`, `--filter "<query>"` |
| Resolve names to IDs | `find-projects` / `find-sections` / `find-labels` | `td project list` / `td section list` / `td label list` (`--json`) |
| Completed tasks | `find-completed-tasks` | `td completed list --since … --until …` |
| Completion history | `find-activity` | `td activity --type task --event completed` |

## Topic search

Text search misses tasks that are about a topic without naming it (a
subtask titled `Step 2: calibrate` under a project's parent task). For a
topic query:

1. If an existing label or project covers the topic, filter by it first.
2. Else, if the settings file (`$TODOIST_SKILLS_CONFIG` or
   `~/.config/todoist-skills/config.toml`) has `[jev] enabled = true`, run
   `python3 scripts/jev_find.py "<concept>" ["<concept>" ...]` (Windows:
   `py -3`) from this skill's own directory. Give one concept per argument;
   a combined query for two unrelated things tends to find neither. It
   fetches active tasks itself and prints only related ones (`p >= 0.65`),
   best first, so the full list never enters the conversation. Add
   `--with-description` only when titles are clearly not enough (it takes
   effect only if `send_descriptions = true`). Treat `p` near 0.65 as
   "possibly related".
3. Otherwise, or on exit 2 (key missing), 3 (not enabled), or any failure:
   search by text and say that topic matching was not available.

Completed tasks are outside the topic path; use the completed-task lookup.

## Reporting results

- Answer the question; do not dump every field. Order or group by what the
  question is about (due date, project, priority).
- For a large result, give the count and the most relevant subset.
- If nothing matches, say so instead of silently broadening the search.
