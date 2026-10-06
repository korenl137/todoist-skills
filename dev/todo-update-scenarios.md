# Plan update scenarios

Review these scenarios when changing session-based plan updates. They are
manual decision checks, not live Todoist tests.

| Request and existing state | Expected behavior |
|---|---|
| “Reflect this session in the plan.” The description lists input validation, error messages, and integration tests. Only input validation was finished. | Mark only input validation done using the existing list format; preserve the other items and keep the task open. Do not add a session-summary comment. |
| “Update the plan we agreed on.” The session confirmed replacing an integration test with an API compatibility check, but merely suggested changing the deadline. | Replace the relevant description item; preserve the deadline and unrelated content. |
| “Reflect the completed validation work.” Validation is an actual child task; two other children remain unfinished. | Read the relevant child tasks and complete only the confirmed finished child. Keep the parent and other children open; do not create a duplicate description checklist. |
| “Update this plan.” The session contains only a proposed scope change and no confirmed progress. | Do not present the proposal as an agreed plan. Ask what to adopt if the requested change remains unclear. |
