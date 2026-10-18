---
name: todo-doctor
description: >
  Audits active Todoist tasks against the user's own label and naming rules
  and flags vague titles, loose related tasks, and stale descriptions.
  Read-only, no automatic fixes. Triggers include "audit my Todoist",
  "check my labels", "find tasks to group", "todoist 라벨 점검", "작업 스타일
  감사", "묶을 작업 찾아줘" (audit sense, not completing or deleting).
  Organization belongs to todo-tidy; project freshness comparison belongs to todo-reconcile.
metadata:
  version: "1.5"
---

# todo-doctor
## Contents

- Tools
- Todoist connection
- Rules come from the user
- What to check
- Read coverage and dates
- Scope
- Reporting
- Follow-up changes


Read-only health check for Todoist task hygiene. It only reports; fixing a
finding requires a separate user request; diagnosis does not authorize writes.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Read active tasks, labels, projects and completed tasks (read-only) | One Todoist route: Todoist MCP or the `td` CLI (read-only login is enough), whichever the user names or `backend` sets | `backend` setting (`mcp` or `td`) to fix the route; Jev audit (`jev_audit.py --todoist`) when `[jev] enabled = true`, which also needs `TODOIST_API_TOKEN` whichever route is chosen | Without Jev, audit the tasks yourself. If the chosen route is unavailable, say so, give its setup, then stop. Report only; never fix. |

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
-g @doist/todoist-cli` (Node 24+) and `td auth login`. Jev is optional;
without it, audit the tasks yourself. The Jev fast path reads tasks through
the Todoist API with `TODOIST_API_TOKEN`, not through either route.

| Step | Todoist MCP | `td` |
|---|---|---|
| Active tasks | `find-tasks` with `filter: "all"` (or `projectId` to narrow), then exclude Inbox | `td task list --all --json` (`--project` to narrow) |
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

1. **Missing action label (legacy only)**: legacy selection and `required_prefix` set, and the task has no
   label with it. A task whose only role is to group subtasks is exempt.
2. **Label outside the rules**: a label in `[labels.retired]`, or not in
   `[labels.allowed]` / `[labels.projects]` / `labels.ignore` when those
   are set.
3. **Project label that does not fit**: a `[labels.projects]` label on a
   task that is clearly not part of that project. Low confidence; report
   as "review".
4. **Vague title**: a bare noun or topic instead of an action one could
   start on. A judgment call. Exempt organizational parents and titles starting with
   the configured non-empty `grouping.header_prefix`; keep their other checks.
5. **Wrong area**: with `[areas]` set, a task clearly belonging to a
   different area than its top-level project. Only clear-cut cases.
6. **Grouping candidate**: with `[grouping] header_prefix` set, two or
   more tasks in one project, not under a header, that share a goal,
   source, or repository. Name the header they could go under.
7. **Stale reference**: a description pointing at something that moved on
   (a local path that no longer exists, a document with a newer dated
   version beside it, "after X" where X is already completed). Check only
   what can be read locally; report the newer fact next to the old one.

In multiple selection mode, no labels or several actions/topics/goals are
valid. Check semantic contradictions, redundant classification and stale state
only when context supports the finding; never enforce one label per role.
Read relevant descriptions/parents/comments before judging state release.
A passed date or a missing optional label is not evidence of readiness.
Disagreements between guide and settings are findings, not a reason to apply
one scheme to selection and a different one to auditing.

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
Exit 4 (invalid settings): report the diagnostic and stop rule-based classification.
On exit 2 (key missing), 3 (not enabled), or a model failure, audit manually
and say the fast path was skipped and why.

## Read coverage and dates

Read every page needed for the requested scope, including child tasks, comments or completion events when relevant.
If a page or source is inaccessible, report partial coverage; do not present a partial count as an exact total or absence as proof.
Resolve relative dates and reporting periods using the user's stated timezone, otherwise the accessible account/session timezone.
For consequential ambiguity, ask; report the absolute date or period and timezone when it affects the result.
Distinguish a task's scheduled date from its deadline and an actual notification.

## Scope

Default to all active tasks except the Inbox, where unsorted tasks are not
yet a violation. Narrow to a project, date range, or label when the user
asks about one.

## Reporting

Group findings by type, not by task, so patterns show. For each, give the
task title, its current labels or project, and the problem. For a large
category, give the count and a few examples. If nothing is wrong, say so;
do not invent nitpicks.

## Follow-up changes

Keep this audit read-only, including when a finding has an obvious fix.
A subsequent request to fix findings is a new authorized edit/organization intent: use todo-update for specified changes or todo-tidy for scoped cleanup when available.
Do not require another blanket approval merely because the request follows an audit; ask about materially ambiguous intent or consequential changes.
If those skills are unavailable, the follow-up can still be handled with the same Todoist route: show concrete changed fields, read current tasks, preserve unrelated content/labels/dates/recurrence/hierarchy, apply only clear authorized edits, and read back results.
Use known retired-label mappings; unexplained removals or missing mappings remain pending rather than silently dropping labels.
After a timeout, inspect current state before retrying and report partial failures.
Independent comparison with current project decisions or implementation belongs to todo-reconcile, beyond this audit's local stale-reference checks.
