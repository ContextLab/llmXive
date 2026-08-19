# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No logging configuration file, script, or code snippet was provided that creates structured logs (e.g., JSON or similar) and routes them both to the `data/results/` directory and the console. The required artifact is missing, so the task is not satisfied.
- **T011** — The required integration test file `tests/integration/test_download_preprocess.py` does not exist in the repository, so the artifact is missing entirely. Without this test, the task’s core deliverable is not provided.
- **T016** — No code, script, or log file was provided showing the added validation logic, the invocation of the T005 utility, or the required error message. Without any artifact to inspect, we cannot confirm that the task’s requirements have been met.
- **T018** — No evidence of a `data/processed/` directory containing saved preprocessed epochs in HDF5 or NPZ format is provided; the claim lacks any actual artifact, file listing, or code that performs the saving step. Consequently the required output is missing.
- **T023** — No code, script, or log file was provided showing the added validation that checks for required electrodes and exits with code 1 while logging the required CRITICAL message. Without such artifact, we cannot confirm the task was fulfilled.
- **T024** — The required artifact `data/metrics/alpha_power.csv` does not exist on disk, so no alpha power metrics have been stored as specified. The task therefore remains unfinished.
- **T025** — The required artifact `data/metrics/plv.csv` does not exist, so no PLV metrics are stored per participant with electrode pair identifiers. The task’s core output is missing.
- **T030** — No code, script, notebook, or results implementing the required correlation logic (VIF check, PCA with joint variance reporting, or partial correlation) were provided. The artifact needed to demonstrate the conditional analysis and its outputs is missing.
- **T034** — declared artifact(s) missing/empty/invalid: data/results/threshold_results.json
- **T035** — declared artifact(s) missing/empty/invalid: data/results/analysis_report.md
- **T037** — No linting output, report, or modified files from the `code/` directory are provided; there is no evidence that ruff was run or that violations were fixed. The required artifact (a clean code state after linting) is missing.
- **T038** — No evidence of any new test files in the `tests/unit/` directory was provided; the claim lacks concrete artifacts (e.g., Python test modules covering N < 30 or missing‑electrode scenarios). The required edge‑case unit tests are missing.
