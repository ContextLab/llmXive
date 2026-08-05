# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No logging configuration file, script, or code snippet was provided that creates structured logs (e.g., JSON or similar) and routes them both to the `data/results/` directory and the console. The required artifact is missing, so the task is not satisfied.
- **T011** — The required integration test file `tests/integration/test_download_preprocess.py` does not exist in the repository, so the artifact is missing entirely. Without this test, the task’s core deliverable is not provided.
- **T016** — No code, script, or log file was provided showing the added validation logic, the invocation of the T005 utility, or the required error message. Without any artifact to inspect, we cannot confirm that the task’s requirements have been met.
- **T017** — The `code/01_download_preprocess.py` file is truncated before the implementation of `check_power_requirements`, so the required logic (halt for N < 30, warning and JSON write for 30 ≤ N ≤ 52) is not present. Additionally, the expected output file `data/results/power_status.json` does not exist. The task’s power‑analysis check is therefore not implemented.
- **T018** — No evidence of a `data/processed/` directory containing saved preprocessed epochs in HDF5 or NPZ format is provided; the claim lacks any actual artifact, file listing, or code that performs the saving step. Consequently the required output is missing.
- **T023** — No code, script, or log file was provided showing the added validation that checks for required electrodes and exits with code 1 while logging the required CRITICAL message. Without such artifact, we cannot confirm the task was fulfilled.
- **T034** — declared artifact(s) missing/empty/invalid: data/results/threshold_results.json
- **T035** — declared artifact(s) missing/empty/invalid: data/results/analysis_report.md
