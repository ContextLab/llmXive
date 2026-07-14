# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No artifact (e.g., script, function, or configuration‑validation module) was provided that checks for the presence of required input files before the pipeline starts. Without such code or documentation, the claim that the task is completed cannot be verified. The implementer must add the actual validation implementation and evidence (e.g., source file, unit test, or usage example).
- **T009** — No `tests/unit/test_data_ingestion.py` file containing the requested `test_imputation_sex_mode_returns_most_frequent` stub is present, and the fixture `tests/fixtures/sample_imputation.csv` is not found. Without these artifacts the task’s requirement is not satisfied.
- **T010** — No `tests/unit/test_data_ingestion.py` file or test stub `test_filtering_excludes_null_primary_outcomes` was presented. Consequently, there is no evidence of a failing test that loads a sample with null `fluid_intelligence` values and checks for a reduced row count. The required artifact is missing.
