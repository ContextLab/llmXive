# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided artifacts include only three of the required core files (`code/__init__.py`, `requirements.txt`, `tests/__init__.py`) and no evidence of the `README.md` file or any of the required directories (`data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`). The task is not fully satisfied.
- **T004** — The provided `code/load_data.py` loads the ASSISTments and OULAD datasets and performs a flexible latency‑feature check, but it never checks for concurrent load labels (e.g., NASA‑TLX scores) nor does it emit the required warning `"Public dataset lacks concurrent load labels. Manual Golden Set (T007g) is required."` Consequently the critical part of the task is missing.
- **T007** — declared artifact(s) missing/empty/invalid: data/processed/golden_set_template.csv
- **T007g** — declared artifact(s) missing/empty/invalid: data/processed/golden_set.csv
- **T007f** — The required `data/processed/golden_set.csv` file is missing and there is no evidence of a validation script that checks for the file (or for a public dataset from T004) and raises the exact HALT error message specified. The task’s core behavior—detecting the missing Golden Set and emitting the precise error—is not demonstrated. Implement a `validate_and_load_golden_set.py` (or equivalent) that performs the checks and raises the exact message, and provide the resulting script/output as proof.
- **T011** — declared artifact(s) missing/empty/invalid: code/config.py
- **T040** — declared artifact(s) missing/empty/invalid: code/analyze_results.py
