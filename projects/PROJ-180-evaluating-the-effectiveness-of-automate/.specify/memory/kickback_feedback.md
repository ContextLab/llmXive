# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'science'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T028 ('Implement Union Ground Truth construction') is marked as unimplemented (checkbox empty). This task is a critical dependency for T027-1 (Alignment) and T032-1 (Metrics), which explicitly depend on `data/processed/ground_truth_union.json`. The absence of this task creates a blocking dependency loop where the core metrics cannot be computed.
- FABRICATED-RESULT signal — projects/PROJ-180-evaluating-the-effectiveness-of-automate/specs/001-evaluating-the-effectiveness-of-automate/tasks.md: self-declared fabricated metric — “…F1 calculation against known mock values and fails initially (expecte…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
