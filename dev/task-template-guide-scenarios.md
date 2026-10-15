# Task template guide validation

These are manual decision and live integration scenarios for the optional guide.
Static review does not establish that an agent reads or follows it.
Run live cases only with authorization for the agent session and temporary Todoist writes.
Keep model/API costs within the authorized scope; Jev is unnecessary for these cases.

## Isolated setup

Use the existing installed skills when their source matches the code under review.
A documentation-only branch needs no checkout switch or skill relinking.
If skill code changes later, isolate that installation separately before testing.

Copy the active config, selected by `TODOIST_SKILLS_CONFIG` or the default config path, into a private temporary directory.
Preserve its backend, label definitions, areas and grouping rules.
Change only the copy's top-level `guide` to an absolute path to the candidate guide, and disable optional Jev in that copy.
Do not copy credentials or change the original config, guide or AEM links.
An existing personal guide remains the production policy; this test evaluates the candidate independently and does not approve replacing that policy.

Select the temporary config through `TODOIST_SKILLS_CONFIG` in the test agent process.
A fresh process is useful for environment isolation, not because every skill caches its settings until restart.
Record the config path, guide revision/diff and selected backend.
Check that the chosen backend is available; do not silently switch routes.
Create no new labels or projects.
If a case needs a label that the config or account lacks, mark that case blocked rather than changing the taxonomy.

## Scope and evidence

Use a unique run marker and record every created task ID.
Explicitly request Inbox for all test fixtures; ordinary placement inference must not move them elsewhere.
Scope every later read, edit and audit to those IDs, including child tasks.
Use no existing personal task as a test fixture.

Read back the stored title, description, labels, priority, due, deadline, project, section and parent after each mutation.
Keep before/after evidence for fields that must be preserved, and record the actual tool operation for the date-only case.
A correct final value alone cannot prove that reschedule was used.
Keep tasks until the results have been reviewed; deleting them first prevents later cloud review.
If a cloud session cannot read local evidence, provide the relevant snapshots explicitly instead of assuming it can access local files.

## Scenarios

| Case | Request and fixture | Pass criteria |
|---|---|---|
| A: research capture | “테스트용으로 Inbox에 조사 작업을 추가해줘. 제목에는 실행 표식을 포함하고, https://example.com 의 제공 자료를 읽고 핵심 세 가지를 정리하는 작업이야. 자료를 이미 읽었다고 쓰지는 마.” | `[조사]` title; type/summary/status header; purpose and binary completion criterion; research questions/output blocks; core blocks in the guide's relative order and type-specific blocks before evidence; URL in evidence block; no invented findings or output paths. Infer only from supplied context. |
| B: literal title | “테스트용으로 Inbox에 제목을 정확히 ‘@home 청소’로 추가해줘. 제목의 @home은 라벨 지정이 아니야.” | Explicit title wins over inferred formatting. Read back the title and labels. If parsing changes them, report original vs stored values and unintended label changes. Record the backend; do not claim another backend behaves identically. If `home` does not exist, do not create the label to make the test pass; record a blocker or observed tool behavior. |
| C: waiting state | Set an initial due on A's task as fixture preparation. Then: “이 테스트 작업을 대기로 바꿔줘. 이유는 교수님 회신 대기, 해제 조건은 회신 도착이야.” | Header becomes waiting; existing labels remain and configured existing `waiting` is added; reason and release condition are recorded; due is cleared. Preserve the remaining description, deadline, hierarchy and placement. |
| C: combined state | On C's waiting fixture: “회신 대기는 유지하고, 내 일정 재검토를 이유로 보류도 추가해줘. 보류 해제 조건은 일정 재검토 완료야.” | Preserve waiting and its reason/release condition; add configured existing on-hold with its separate reason/release condition; header becomes 대기·보류. Do not change dates or unrelated labels. |
| C: release waiting only | From the combined state: “회신이 도착했으니 회신 대기만 해제해줘. 일정 재검토는 아직 안 끝났어.” | Remove only waiting; preserve on-hold and its unresolved condition; header becomes 보류. Do not claim the task is ready or change dates. |
| C: release hold only | Independently restore the combined fixture, then: “일정 재검토는 완료했지만 회신은 아직 안 왔어. 보류만 해제해줘.” | Remove only on-hold; preserve waiting and its unresolved condition; header becomes 대기. Do not change dates. |
| C: unknown release | From a combined fixture with no new release evidence: “현재 상태를 점검해줘.” | Report-only inspection preserves both labels, their separate conditions and the 대기·보류 header; lack of evidence does not release either state. |
| D: date only | Create a separate non-waiting task with a description, existing labels and a due. Snapshot it. Then: “이 테스트 작업의 계획일(due)만 다음 주 월요일로 옮겨줘. 마감일(deadline), 설명, 라벨, 프로젝트, 부모는 그대로 둬.” | Use reschedule. Only due changes; no template normalization, new status block, relabeling or move. Record the absolute target date and timezone. Do not reuse C's waiting task. |
| E: scoped audit | Create a parent with a clear result-noun title and a meaningful child action. Then: “이번 실행의 테스트 ID들만 라벨·제목 점검해줘. Inbox도 명시적으로 포함하고, 다른 작업은 점검하거나 수정하지 마.” | The audit actually includes the test IDs. Do not flag a parent merely for lacking a verb. Do not flag absent optional example labels as config conflicts. Report genuine findings only; write nothing. |
| E: conflict detection | For a second read-only audit, use another temporary config/guide pair with an explicit mandatory label rule that contradicts its allowlist. Scope to the same IDs. | Report the config/guide disagreement without creating labels or changing tasks. Do not use the genuine production config as a broken fixture. Restore the normal test-config selection afterward. |
| F: cleanup | After reviewing A–E and saving evidence: “이번 실행에서 만든 테스트 작업들을 삭제해줘.” | Identify exact IDs and count children/comments before asking for confirmation. Delete only after confirmation; account for parent/child cascading so unrelated tasks are preserved. Read back or query to confirm removal. |

Completion-guide behavior is excluded: `todo-complete` currently lacks guide loading.
Do not count its normal delete confirmation as proof that completion-guide rules work.

## Results

Record the run marker, agent/product, installed skill revision, candidate guide revision/diff, backend, config selection, time and timezone.
For each case record pass, fail, blocked or not run with evidence and any tool errors.
Separate guide contradictions, missing skill instructions and backend behavior; a single unsuccessful run does not identify its cause by itself.
Record remaining test IDs if cleanup is pending.
Merge and production-guide adoption are separate decisions after reviewing the results.
