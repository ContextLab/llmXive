# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — There are no unit test files, test suites, or any code artifacts provided that target the project's configuration or logging utilities. The only evidence shown relates to avian vocal‑complexity feature specifications, not to unit tests for config/logging, so the required tests are missing.
- **T015** — The required output files `data/interim/noise_mapped.csv` and `data/interim/dropped_missing_osm.csv` are not present on disk, so the task’s deliverables are missing despite the presence of `src/data/acquisition.py`.
- **T015c** — declared artifact(s) missing/empty/invalid: data/interim/validation_log.csv
- **T018b** — declared artifact(s) missing/empty/invalid: data/interim/species_filtered.csv
- **T019** — declared artifact(s) missing/empty/invalid: src/data/extraction.py
- **T020** — The required output file `data/processed/final_dataset.csv` does not exist, and the schema file `contracts/dataset.schema.yaml` is also missing. Moreover, the provided `src/data/preprocessing.py` is truncated and does not show the logic for combining filtered data, extracting metrics, saving the final CSV, or invoking validation against the specified schema. These essential artifacts and functionality are absent.
- **T022** — The provided `tests/contract/test_output_schema.py` is present but the implementation of `test_numeric_columns_are_valid` is truncated, so the test suite is incomplete. Additionally, the required `data/processed/model_results.csv` file is missing, causing the existence check to fail. The test file must be fully implemented (including the numeric‑column validation logic) and the CSV file must be present for the contract test to pass.
