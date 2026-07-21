# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — There are no unit test files, test suites, or any code artifacts provided that target the project's configuration or logging utilities. The only evidence shown relates to avian vocal‑complexity feature specifications, not to unit tests for config/logging, so the required tests are missing.
- **T014** — declared artifact(s) missing/empty/invalid: src/data/acquisition.py
- **T015** — The required `src/data/acquisition.py` script does not exist, and the expected output files `data/interim/noise_mapped.csv` and `data/interim/dropped_missing_osm.csv` are also missing. Consequently, the task’s core functionality and deliverables are not present.
- **T015c** — declared artifact(s) missing/empty/invalid: data/interim/validation_log.csv
- **T017a** — The `filter_by_snr_threshold` function in `src/data/preprocessing.py` is only partially shown (truncated) and does not contain a concrete implementation that reads, filters, and writes the CSV files. Moreover, the required output file `data/interim/filtered_snr.csv` is absent from the repository. Both the core logic and the expected artifact are missing, so the task is not genuinely completed.
- **T017b** — declared artifact(s) missing/empty/invalid: data/interim/filtered_snr.csv
- **T021** — The required artifact `data/interim/dropped_records.csv` does not exist on disk, so the logging of excluded records cannot be verified. The implementer must create the CSV file with the appropriate records to satisfy US‑1 Acceptance Scenario 3.
- **T022** — The provided `tests/contract/test_output_schema.py` is present but the implementation of `test_numeric_columns_are_valid` is truncated, so the test suite is incomplete. Additionally, the required `data/processed/model_results.csv` file is missing, causing the existence check to fail. The test file must be fully implemented (including the numeric‑column validation logic) and the CSV file must be present for the contract test to pass.
- **T023** — The required artifact `tests/unit/test_loso_cv.py` does not exist in the repository, so the unit test for LOSO cross-validation split logic is missing. The task cannot be considered completed until this file is added with appropriate test code.
