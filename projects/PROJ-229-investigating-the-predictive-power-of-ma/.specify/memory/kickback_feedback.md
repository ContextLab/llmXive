# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'science'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T013 instructs writing an 'empty file' to `data/external/literature_pcms_raw.csv` if the DOI is inaccessible. This violates Constitution Principle III (Data Hygiene) which requires raw data to be checksummed and preserved; an empty file breaks the checksum/traceability chain. While the task exists, its implementation logic contradicts the constitutional constraint it is meant to satisfy.
- FABRICATED-RESULT signal — projects/PROJ-229-investigating-the-predictive-power-of-ma/specs/001-investigating-the-predictive-power-of-ma/tasks.md: self-declared fabricated metric — “…If `config.yaml` contains the placeholder value (e.g., 10), set a flag `resea…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
