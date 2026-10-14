---
name: todo-find
description: >
  Looks up and lists Todoist tasks by date range, project, label, search
  text, or topic; also answers what was completed. Read-only. Triggers
  include "what's on my list today", "show this week's tasks", "find tasks
  about X", "what did I finish", "오늘 할 일 뭐 있어", "이번 주 작업 목록
  보여줘", "완료한 작업 보여줘".
metadata:
  version: "1.3"
---

# todo-find
## Contents

- Tools
- Todoist connection
- Topic search
- Grouped answers
- Reporting results


Look up Todoist tasks. Read-only: never changes anything, so no
confirmation is needed.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Read tasks and completion history (read-only) | One Todoist route: Todoist MCP or the `td` CLI (read-only login is enough), whichever the user names or `backend` sets | `backend` setting (`mcp` or `td`) to fix the route; Jev topic search (`jev_find.py`) when `[jev] enabled = true`, which also needs `TODOIST_API_TOKEN` whichever route is chosen; label meanings from settings for topic matches and groups, no Jev | Without Jev, match by label meaning, or search by text, project and label. If the chosen route is unavailable, say so, give its setup, then stop. |

## Todoist connection

Use the route the user names in the request, for that request only. Otherwise
use `backend` from settings: `mcp` (Todoist MCP) or `td` (the td CLI)
(read-only login is enough). Neither route is preferred. When `backend` is
set, use that route without a question; if it is unavailable, say so and give
its setup, then stop; do not switch routes silently. When `backend` is unset
or holds any other value and only one route is available, use it without a
question. When both are available, ask once, in the user's language: "Todoist
작업을 어떤 경로로 처리할까요? 1) Todoist MCP 커넥터 2) td CLI". Apply the answer to this
request only and write nothing to any file. Then add one line: to stop this
question, put `backend = "mcp"` or `backend = "td"` in your settings file. If
neither route is available, say how to connect each one and stop. To connect
Todoist MCP, connect Todoist in your agent. To set up `td`, run `npm install
-g @doist/todoist-cli` (Node 24+) and `td auth login`. Jev topic search is
optional; it reads tasks through the Todoist API with `TODOIST_API_TOKEN`, not
through either route.

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
2. Else, match the topic against the meaning of each label in
   `[labels.allowed]` (for example `topic/food` = "recipes, cooking,
   groceries") and filter by the labels whose meaning fits. This needs no
   Jev. Say which labels were used, and that tasks about the topic without
   those labels are not included.
3. Else, if the settings file (`$TODOIST_SKILLS_CONFIG` or
   `~/.config/todoist-skills/config.toml`) has `[jev] enabled = true`, run
   `python3 scripts/jev_find.py "<concept>" ["<concept>" ...]` (Windows:
   `py -3`) from this skill's own directory. Give one concept per argument;
   a combined query for two unrelated things tends to find neither. It
   fetches active tasks itself and prints only related ones (`p >= 0.65`),
   best first, so the full list never enters the conversation. Add
   `--with-description` only when titles are clearly not enough (it takes
   effect only if `send_descriptions = true`). Treat `p` near 0.65 as
   "possibly related".
4. Otherwise, or on exit 2 (key missing), 3 (not enabled), or any failure:
   search by text and say that topic matching was not available.

Completed tasks are outside the topic path; use the completed-task lookup.

## Grouped answers

Read the configured settings for meaning/role rules. When a relevant guide is
named, resolve relative paths from the config directory and apply its task
conventions; keep current user decisions above historical guide rules.

Match the requested intersection (both labels) or union (either label).
In multiple selection mode, use meanings/roles from settings rather than a
name prefix. Group by the requested purpose; do not always force action first.
Legacy mode keeps required_prefix action grouping, with area grouping when set.

Deduplicate task IDs in unions. One task can contribute to multiple label groups;
show the overlap and unique total instead of adding group counts as total work.
For completed work, count dated completion occurrences/events and distinguish
recurrences of the same task; task IDs alone do not identify those occurrences.
Task counts are not time spent, progress percentages or research outcomes.

Separate stored labels, classification inferred from task/parent context, and
unclassified items. Missing optional action labels are normal; do not silently
write an inferred label. A label-only search does not cover unlabeled related
work: disclose the scope or inspect relevant parent/description context when
the user asked for broader coverage. Parent labels are not stored child labels.

For executable-work queries, inspect relevant dependencies and conditions.
The absence of waiting/on-hold is not proof of readiness; report unverified
conditions separately. Do not change any task while interpreting its state.
Invalid settings (exit 4 from a helper) are a reported gap, not permission to
substitute an assumed taxonomy.

## Reporting results

- Answer the question; do not dump every field. Order or group by what the
  question is about (due date, project, priority).
- For a large result, give the count and the most relevant subset.
- If nothing matches, say so instead of silently broadening the search.
