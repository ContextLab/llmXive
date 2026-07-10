# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'science'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Tasks T028 and T029 are identical duplicates ('Implement code/analyze.py to perform t-tests and ANOVA...'). An implementer cannot deterministically choose which to execute or split the work. This creates ambiguity in task ownership and violates the 'Concrete deliverable' criterion.
- Task T033 creates a circular dependency by requiring T028-T032 (analysis logic) to be complete before it can run, yet T028-T032 require T033 (corrupted data generation) to be complete. This structural flaw prevents the execution of the core simulation loop required by FR-002 and FR-004, violating the requirement for a functional pipeline.
- Tasks T028 and T029 are identical duplicates ('Implement code/analyze.py to perform t-tests and ANOVA...'). This redundancy creates ambiguity in task ownership and violates the principle of a clear, non-redundant task list required to satisfy the spec's execution flow without confusion.
- FABRICATED-RESULT signal — projects/PROJ-427-evaluating-the-robustness-of-statistical/specs/001-evaluating-the-robustness-of-statistical/tasks.md: self-declared fabricated metric — “…synthetic_metadata.json`, not hardcoded values, and MUST include CI coverag…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
