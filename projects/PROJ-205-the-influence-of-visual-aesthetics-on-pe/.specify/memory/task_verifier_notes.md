# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T024a** — The repository contains `code/analysis/00_preprocess.py`, but the required input file `data/raw/submissions.csv` does not exist, and the script has not produced the expected output `data/processed/cleaned_data.csv`. Without the raw data and the generated cleaned CSV, the preprocessing task is not fulfilled.
- **T045** — declared artifact(s) missing/empty/invalid: data/processed/power_analysis_results.json, data/processed/cleaned_data.csv
- **T048** — The required `data/processed/analysis_results.json` file does not exist, and the provided excerpt of `code/analysis/02_pairwise.py` does not show the new `--correction-method` command‑line argument (its parser is missing from the visible code). Both artifacts needed to satisfy the task are absent or incomplete.
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/mixed_effects_results.json
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/mixed_effects_results.json
- **T049** — declared artifact(s) missing/empty/invalid: code/analysis/_mixed_effects.py, data/processed/mixed_effects_results.json
- **T052** — The provided `03_mixed_effects.py` does not contain any convergence‑checking, retry‑with‑different‑optimizers, or simplified random‑effects logic, nor does it write results to `data/processed/mixed_effects_results.json`. Moreover, the required `mixed_effects_results.json` file is absent. The task’s core requirements are therefore unmet.
- **T043c** — The test `tests/benchmark/test_runtime.py` contains the required size assertion, but the dependent file `data/raw/submissions.csv` is absent, so the assertion cannot be evaluated and the task’s prerequisite is unmet. The missing CSV file must be provided for the task to be considered complete.
- **T051c** — Both required files `data/processed/analysis_results.json` and `data/processed/mixed_effects_results.json` are missing, so the schema updates cannot be verified. The task needs these JSON files present and containing the new `ci_lower` and `ci_upper` keys.
