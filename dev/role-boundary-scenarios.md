# Role boundary scenarios

These are manual decision checks for routing and preservation, not proof of live agent behavior.
Use per-skill evals for standalone cases; a missing neighboring skill must not require reading its files.

| Request | Owner and expected result |
|---|---|
| “오늘 작업 보여줘” | todo-find; paginated lookup, no writes. |
| “라벨 규칙 점검해줘” | todo-doctor; findings only. |
| “방금 점검한 명확한 라벨 오류 고쳐줘” | todo-tidy for scoped organization or todo-update for specified edits; no repeated blanket approval. |
| “이 작업 날짜만 다음 금요일로” | todo-update; resolve timezone/date and reschedule while preserving recurrence and format. |
| “이번 세션에서 확정된 변경만 반영해줘” | todo-update; no independent project investigation. |
| “프로젝트 최신 변경과 이 태스크를 대조해줘” | todo-reconcile; source-backed comparison, no writes or template normalization. |
| “최신 변경 대조 후 명확한 차이는 반영해줘” | todo-reconcile comparison plus safe update; unsupported scope changes stay pending. |
| “서식이 안 맞는 작업에 내 템플릿 적용해줘” | todo-tidy; configured guide, useful content retained, no invented facts. |
| “최신 내용과 맞추고 템플릿도 적용해줘” | Reconcile relevant facts, then tidy requested format; do not treat either as permission to complete tasks or change incidental dates. |
| “이 작업의 설명만 지정한 형식으로 바꿔줘” | todo-update; exact scoped formatting edit. |
| “같은 작업 등록해줘” with an equivalent existing task | todo-add; show existing task and resolve whether a distinct new task is intended. |
| “다 끝났어, 작업 갱신해줘” | Completion intent permits todo-update to record the requested note and complete; do not force a second invocation. |
| Creation/completion timed out | Inspect stored state or dated completion occurrence before retry; no duplicate creation or double recurrence advancement. |
| Requested results span more than one page or a source is unreadable | Fetch necessary pages; state coverage limits and avoid false exact totals/freshness claims. |

A source proposing work is not confirmation; a merged change is not alone proof of acceptance.
No skill should infer that an unlabelled task is executable or that a passed date releases waiting/on-hold.
