# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T009 does not specify which multiple‑comparison correction method (Bonferroni or Benjamini‑Hochberg) to apply when >1 hypothesis is tested, making the verification nondeterministic. The task should explicitly state the correction method to ensure reproducible, testable output.
- FR-001 requires downloading bulk configuration files from **both** Materials Project and OQMD. Task T003 only downloads OQMD records and never attempts Materials Project retrieval, thereby weakening the functional requirement.
- FR-011 mandates validation of EAM‑derived segregation‑energy labels against a DFT benchmark of ≥30 samples with MAE ≤ 0.1 eV. No task in the list implements this validation step; the pipeline merely records a `[DATA_UNAVAILABLE]` status, which does not meet the requirement.
- Constitution Principle VI (Materials Data Provenance) requires sourcing bulk configuration and grain‑boundary datasets from **both** Materials Project and OQMD. The current task set only uses OQMD, constituting a constitutional drift.
