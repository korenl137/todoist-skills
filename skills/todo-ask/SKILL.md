---
name: todo-ask
description: >
  Reviews the whole Todoist account, researches linked material for review
  tasks, and walks the user through updates and completions with short
  multiple-choice questions. Use when the user wants a full task review with
  questions, e.g. "태스크 전체 점검해줘", "투두이스트 문답으로 정리", "인박스 정리하고
  물어봐줘", "review all my tasks and ask me". Organizing a scope without
  questions belongs to todo-tidy, a single edit to todo-update, a plain
  lookup to todo-find, and a read-only rule audit to todo-doctor.
metadata:
  version: "1.0"
---

# todo-ask

## Contents

- When to use
- Tools
- Todoist connection
- Flow
- Rules

Review everything, research what needs reading, ask, then apply only what the
user answered. This skill owns the flow; field rules stay with the sibling
skills.

## When to use

Use for a full or inbox-plus-schedule review where the user expects questions.
Do not use for one named edit (todo-update), a quiet reorganization of a
scope (todo-tidy), a lookup (todo-find) or a rules audit (todo-doctor).
Each skill works alone: when a sibling is installed, follow it for its
responsibility; when not, apply the same field rule from this file without running the review flow.

## Tools

| Need | Required | Recommended | Fallback |
|---|---|---|---|
| Read and change tasks, comments, projects, sections | One Todoist route: MCP or `td` | Live schemas; paginated reads | If the selected route is unavailable, say so and stop; never switch silently |
| Multiple-choice questions | None | AskUserQuestion | Numbered text questions, same content; a missing question tool is not an unattended run |
| Linked material | Accessible link or document | Page, video transcript or document read | Say it was not read; never guess its content |

## Todoist connection

Use the route the user names; otherwise `backend` from
`$TODOIST_SKILLS_CONFIG` or `~/.config/todoist-skills/config.toml` (`mcp` or
`td`). With neither, use the single available route; if both exist, ask once
for this request. Read the settings and, if it names a `guide`, the guide
(relative paths resolve beside the settings file); the user's words win.
Follow the same route for every call below.

## Flow

1. **Read, no writes.** Inbox; project and section descriptions (they decide
   placement; read the project itself as well as its sections); overdue plus
   the next 7 days; tasks completed today, including recurring occurrences
   (use the activity log with the user's ID from user-info and the account
   timezone, not only the completed list); tasks created in the
   last 2 days; p1, overdue, and undated p2. Read every page, and report
   partial coverage instead of exact totals.
2. **Research first** (comments are posted in attended runs only; an unattended
   run reports the findings instead). For any open task whose purpose rests on a link,
   video or shared document (a link-only Inbox capture: read its link and
   comments to judge its purpose, and research only when the purpose is a review; any task titled `[검토]` among those read in step 1), read its comments first. Research comments start with the heading
   `## 조사 정리 (YYYY-MM-DD)`; if one exists, skip the task unless the user asks for
   an update. Otherwise read the material and post the result
   as a **comment**, never in the description. Put the scope at the top (read, not read, substituted),
   findings in the middle, and the decisions the user must make last. Do not
   guess the content of anything unread; say why it was unreadable.
3. **Report findings.** Overdue; due today; overloaded days (the account's daily goal from user-info, else state your
   threshold; count every task due that day, children included, and say so); undated tasks
   with a deadline; start/finish dates in the wrong order; stale descriptions
   (references to finished or dropped work); tasks completed by mistake
   (the status header is anything but done or 검증 대기, or a `## 완료 기준`
   condition is unmet); recurring times that no longer match the schedule the description states; label or
   section mismatches against the guide (report them; replace a retired
   label only with its mapped replacement; with no mapping, or a label the
   settings do not list, keep it and ask; several such labels may share one question).
4. **Ask.** At most 4 questions per round; pick the highest-consequence items for the
   round and list the rest as findings with an offer of another round. Each question names the task and
   its current value so it stands alone, puts the recommended answer first,
   and uses free text when the answer is not a choice. Within the round, order the
   questions yes/no, missing information, dates, decisions; the recommended answer is
   the first option inside each question. Without AskUserQuestion, say once
   that you are asking in text. If the user asks for everything at once,
   run rounds back to back and apply at the end. A free-text answer beats the
   listed options. A fact you or the user need confirmed (a deadline, a
   source, whether something already happened) is looked up with tools first;
   ask only when tools cannot settle it.
5. **Apply.** Only what the answers settle, the inbox organization plan below
   and the assumption note in Rules (in an all-at-once run, apply at the end):
   - Title, description and section moves for inbox organization: show the
     plan first (current to proposed), then apply clear items without a
     separate answer, including replacing a retired label with its mapped
     replacement. This follows
     todo-tidy and the configured guide for title and description format.
   - Dates, priority, other labels: only as answered; resolve relative dates
     in the account timezone and report the absolute date. A date-only move of a dated task uses the
     reschedule operation so recurrence survives; a task with no date cannot
     be rescheduled, so set its first date with the date field (it has no
     recurrence to lose).
   - Completion: only as answered, following todo-complete and each task's
     `## 완료 기준` block when the guide defines one.
   - Description edits are block-level: read the current text, change the
     named blocks, and send the whole text with unchanged blocks verbatim.
     Send Korean text as plain characters, never escaped, and read it back
     for typos.
   - Update the description's status header when the status changes. Record
     the date and the decision of a status change in a comment (history
     lives in comments, per the guide), not in a new description block;
     completions get no comment unless the user asks.
6. **Report.** What was done (numbered), what still needs the user, the next
   step. No internal IDs.

## Rules

- Never complete, delete, reschedule or change priority without an answer to
  that exact question; a delete or parent-completion question states the
  child-task and comment counts (todo-complete). Never create labels; create
  sections only when the user names a project and asks for them (todo-tidy).
- A date assumed from a source never goes in the title or the due field.
  Note it in a comment as an assumption (source, unconfirmed) and ask the
  user to confirm it in this round if a slot remains, otherwise the next, and
  skip the question if tools settle it. This note and the step 2 research
  comments are the only writes allowed before an answer.
- The user's own conventions override this flow. If a task or section
  description says how it is handled, follow it.
- In a scheduled or unattended run there is nobody to answer: read, research
  and report only. Make no task changes, comments and the assumption note
  included; put research findings in the report instead.
- Read back changed tasks and compare changed fields, preserved metadata
  (recurrence, labels, section) and hierarchy. After a timeout, read the task before retrying.
