# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — No `fetch_data.py` or `preprocess.py` files containing a checkpoint mechanism are present in the provided evidence; the claim lacks any code, configuration, or documentation showing state‑saving after each game. Consequently the required artifact is missing.
- **T010** — The test file `code/tests/test_preprocess.py` is present, but the required contract file `run_record.schema.yaml` does not exist in the repository (the note explicitly says “schema.yaml: MISSING”). Without the actual schema file, the test cannot perform real contract validation, so the task is not fully satisfied.
- **T023** — The required schema file `contracts/distribution_fit.schema.yaml` is missing, and there is no evidence of a `distribution_fits.csv` file or any validation being performed. Without these artifacts, the task cannot be considered completed.
- **T029b** — declared artifact(s) missing/empty/invalid: code/scripts/generate_report.py
- **T033a** — No `fetch_data.py` file or any diff showing refactored pagination logic is present; the claim cannot be verified because the required artifact is missing. The next implementer must provide the updated `fetch_data.py` with clearly refactored pagination code.
- **T033b** — No code artifact was provided showing that a `calculate_lagged_pressure` function was extracted from `preprocess.py`; the repository contents are not displayed, and there is no evidence of the refactored file or new function implementation. The required refactoring artifact is missing.
