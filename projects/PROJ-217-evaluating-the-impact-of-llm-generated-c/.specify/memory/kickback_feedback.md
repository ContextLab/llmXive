# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The design assigns each code snippet to only one comment condition (LLM, human, or none) while participants are randomized once to a single condition for the entire study. This conflates snippet difficulty with comment type, creating a confound that prevents causal attribution of performance differences to the comment condition. A valid causal inference requires that each snippet be evaluated under all conditions (within‑subject or counterbalanced across participants) or that snippets be randomly balanced across conditions with sufficient replication.
- FR-006 (validate availability and relevance of the data collection environment and participant recruitment tools before the user study) has no corresponding phase, task, or contract in the implementation plan. No step explicitly checks recruitment platform access, consent workflow, or environment setup, leaving this functional requirement unaddressed.
- The plan states that `human_study_responses.csv` must conform to `contracts/analysis.schema.yaml`, but the `analysis.schema.yaml` defines the schema for analysis result files, not for the raw human study data. The correct contract is `contracts/dataset.schema.yaml`. This mismatch will cause schema validation to fail.
- Phase 7 only mentions validating all output files against `contracts/analysis.schema.yaml`. It should also validate the merged dataset (`analysis_dataset.csv`) against `contracts/dataset.schema.yaml` to ensure full contract coverage.
