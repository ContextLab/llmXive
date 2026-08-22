# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'science'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T042 is marked as rejected in the 'Revision Note' yet remains in the active task list as '- [ ] T042'. It lacks a revised implementation plan to produce `results/validation_report.json` with the specified schema and exit logic, leaving the data validation requirement unfulfilled.
- Task T030 mandates raising a `FileNotFoundError` if manual annotations are missing, contradicting the spec (SC-005) which allows an 'expert review report' fallback. This makes the task non-executable in scenarios where annotations are missing but the project should proceed via the fallback path defined in the spec.
- Task T032 mandates calculating confidence intervals using residuals from the 'validation set' for 'test set' predictions. This contradicts the spec (FR-008) and introduces data leakage risks, making the task's statistical logic invalid and non-executable as a correct implementation of the requirement.
- Task T005 ('Implement batch loading strategy') is too coarse. It describes a high-level goal ('prevent OOM') and references a dependency but does not name the specific artifact (e.g., a custom `DataLoader` class or specific function signature) or the exact logic to be implemented. The atomizer will need to split this.
- FABRICATED-RESULT signal — projects/PROJ-477-predicting-material-strength-from-micros/specs/001-predicting-material-strength-from-micros/tasks.md: self-declared fabricated metric — “…sh and compare it against the hardcoded value in `config.yaml`. If mismatch…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
