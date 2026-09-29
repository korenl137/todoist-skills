---
name: todo-doctor
description: >
  Audits active Todoist tasks against the user's own label and naming rules
  and flags vague titles, loose related tasks, and stale descriptions.
  Read-only, no automatic fixes. Triggers include "audit my Todoist",
  "check my labels", "find tasks to group", "todoist 라벨 점검", "작업 스타일
  감사", "묶을 작업 찾아줘" (audit sense, not completing or deleting).
metadata:
  version: "1.1"
---

# todo-doctor

Read-only health check for Todoist task hygiene. It only reports; fixing a
finding is a separate request that needs confirmation.

## Todoist connection

Use the `backend` setting when present; otherwise use Todoist MCP if
available, then the authenticated `td` CLI (read-only login is enough).
If neither is available, tell the user to connect Todoist MCP or install
`td` (`npm install -g @doist/todoist-cli`, Node 24+) and run `td auth login`.
Jev is optional; without it, audit the tasks yourself.

| Step | Todoist MCP | `td` |
|---|---|---|
| Active tasks | `find-tasks` | `td task list --all --json` (`--project` to narrow) |
| Labels / projects | `find-labels` / `find-projects` | `td label list --json` / `td project list --json` |
| Completed tasks (for stale references) | `find-completed-tasks` | `td completed list --search "…" --json` (`--search` cannot be combined with `--since`/`--until`) |

## Rules come from the user

Read the settings file (`$TODOIST_SKILLS_CONFIG` or
`~/.config/todoist-skills/config.toml`) and, if it names one, the `guide`
file, fresh on every run; they can change. Where the guide's prose and the
settings lists disagree, report the disagreement as a finding. Without any
settings, audit only what needs no rules: checks 4, 6, and 7, plus labels
that exist on tasks but nowhere in the label list.

## What to check

1. **Missing action label**: `required_prefix` set, and the task has no
   label with it. A task whose only role is to group subtasks is exempt.
2. **Label outside the rules**: a label in `[labels.retired]`, or not in
   `[labels.allowed]` / `[labels.projects]` / `labels.ignore` when those
   are set.
3. **Project label that does not fit**: a `[labels.projects]` label on a
   task that is clearly not part of that project. Low confidence; report
   as "review".
4. **Vague title**: a bare noun or topic instead of an action one could
   start on. A judgment call.
5. **Wrong area**: with `[areas]` set, a task clearly belonging to a
   different area than its top-level project. Only clear-cut cases.
6. **Grouping candidate**: with `[grouping] header_prefix` set, two or
   more tasks in one project, not under a header, that share a goal,
   source, or repository. Name the header they could go under.
7. **Stale reference**: a description pointing at something that moved on
   (a local path that no longer exists, a document with a newer dated
   version beside it, "after X" where X is already completed). Check only
   what can be read locally; report the newer fact next to the old one.

### Jev fast path (only when `[jev] enabled = true`)

For a full audit, first run `python3 scripts/jev_audit.py --todoist`
(Windows: `py -3`) from this skill's own directory. It fetches active
non-Inbox tasks itself, so the list never enters the conversation, and
returns checks 1–2 (computed) and 3–5 (Jev judgments from titles and
parent titles; descriptions are not sent). For a narrower scope, pipe
`{"tasks": [{"id", "title", "labels", "project": "Parent / Name",
"parent_title"?, "has_children"?}]}` into it without `--todoist`.

Present Jev findings as "review" and drop one only when the user's rules
clearly say otherwise. Run checks 6–7 yourself; they need descriptions.
On exit 2 (key missing), 3 (not enabled), or any failure, audit manually
and say the fast path was skipped and why.

## Scope

Default to all active tasks except the Inbox, where unsorted tasks are not
yet a violation. Narrow to a project, date range, or label when the user
asks about one.

## Reporting

Group findings by type, not by task, so patterns show. For each, give the
task title, its current labels or project, and the problem. For a large
category, give the count and a few examples. If nothing is wrong, say so;
do not invent nitpicks.

## Fixing findings

Only on a separate request. Treat each fix as a normal edit (label lists
are replaced, so send the full new list; never change a due date through
the due string). Show the per-task change and get confirmation before a
bulk change. Replace a retired label only with its mapped replacements from
`[labels.retired]` (comma-separated); when the mapping is empty or missing, propose one per
task and let the user decide. Never drop a label silently.
