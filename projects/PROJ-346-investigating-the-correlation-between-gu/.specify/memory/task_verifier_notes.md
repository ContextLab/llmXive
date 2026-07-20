# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No pytest configuration file (e.g., `pytest.ini` or `conftest.py`) or test runner script was presented, and the provided project excerpt concerns data ingestion rather than test setup. The required artifacts are missing, so the task is not satisfied.
- **T015** — The `code/02_preprocess.py` file is truncated and does not contain a complete outlier‑filtering implementation nor any code that writes a log to `data/qc/filtering_log.json`. Moreover, the required `filtering_log.json` file is absent from the repository. The task’s core requirement is therefore unmet.
- **T016** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009a** — The required file `tests/unit/test_imputation.py` is missing from the repository, so the unit tests for MICE imputation and z‑score normalization do not exist. Without this artifact, the task’s deliverable is not present.
- **T010a** — The required artifact `tests/integration/test_merge.py` does not exist in the repository, so the integration tests for `test_linkage_failure_detection` and `test_gap_report_trigger` are missing. The task cannot be considered completed until this file is added with the specified tests.
- **T020** — The required artifact `tests/unit/test_regression.py` does not exist in the repository, so no unit test for the LASSO/Elastic Net regression is present. The implementer must add a non‑empty test file at that location that validates the regression functionality.
- **T023** — The script exists but its missing‑data handling logs a generic warning (“Merged dataset not found … Skipping regression analysis.”) instead of the required exact message “N/A - Data Gap”. Consequently the implementation does not meet the specified logging requirement.
