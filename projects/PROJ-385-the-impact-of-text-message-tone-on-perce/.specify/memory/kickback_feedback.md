# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'science'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T027 (Define sensitivity definitions) has 'Dependency: None'. However, T028 (Sensitivity analysis engine) depends on T027. T028 also depends on T025 (Analysis Results). T025 depends on T020, T021, T023a. T020 depends on T016. T016 depends on T015b. The chain is T015b -> ... -> T025 -> T028. T027 is independent of the data flow, which is correct (definitions can be static). However, T027 description mentions 'UNRESOLVED-CLAIM: c_d7e061e5'. This claim status does not affect the ordering, but the task is marked as '[P]' (parallel-safe). T027 can run in parallel with T020-T025, which is correct. The ordering is valid.
- FABRICATED-RESULT signal — projects/PROJ-385-the-impact-of-text-message-tone-on-perce/specs/001-the-impact-of-text-message-tone-on-perce/tasks.md: self-declared fabricated metric — “…i.csv` at runtime. Do NOT use hardcoded values like '40'.  3. **Missing Dat…”. Research results must be REAL measurements, never simulated / placeholder / hardcoded / drawn from random.*. The reviser must replace this with a genuine computation before the stage advances.
