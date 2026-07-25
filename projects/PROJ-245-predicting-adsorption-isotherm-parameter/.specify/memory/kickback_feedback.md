# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'science'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T014z creates a hardcoded lookup table for descriptors (Kinetic Diameter, etc.) from 'verified literature'. While this provides values, the spec FR-001 and Constitution Principle VI mandate that descriptors be *calculated* using RDKit in `code/`. The task description implies a lookup approach which conflicts with the 'calculate' requirement, creating a potential implementation gap where the 'calculation' logic is bypassed for these specific descriptors.
- Task T035a requires manual curation of `kr_cnt.csv` because 'no verified URL/DOI exists'. This contradicts Constitution Principle III (Data Hygiene) which requires checksummed, immutable raw data and documented derivations, and Principle I (Reproducibility) which demands fetching from canonical sources. The task description admits to a non-reproducible manual entry process, which is a violation of the project's own constraints, though the task itself exists.
- FABRICATED-RESULT signal — projects/PROJ-245-predicting-adsorption-isotherm-parameter/specs/001-predicting-adsorption-isotherm-parameter/tasks.md: self-declared fabricated metric — “…z provides the provenance for hardcoded values. - **Critical**: T014b/c/d p…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
