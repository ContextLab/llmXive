# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directory hierarchy (`data/raw`, `data/processed`, `results/models`, `results/reports`, `results/plots`, `code`, `tests`) is provided; the claim lacks any artifact listing or screenshots confirming the folders exist. The task cannot be considered complete until the actual project directories are created and shown.
- **T003** — The implementer provided only the feature specification and user‑story details; there are no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) and no evidence that flake8/black have been set up or run. These required artifacts are missing, so the task is not satisfied.
- **T009** — No evidence of the required directory hierarchy (`data/raw`, `data/processed`, `results/models`, `results/reports`, `results/plots`) is present in the provided artifacts; the implementer did not supply any files or listings showing these folders exist. The task therefore remains unfulfilled.
- **T018** — declared artifact(s) missing/empty/invalid: tests/unit/test_model.py
- **T019** — The required artifact `tests/unit/test_model.py` does not exist on disk, so no unit test for the Bonferroni and Benjamini‑Hochberg correction logic is provided. The task therefore remains unfinished.
- **T023** — The repository lacks the required `data/processed/enriched.csv` file, and `code/model.py` does not contain a `train_model` CLI command (only helper functions are present). Both the input data and the specified CLI entry point are missing, so the task is not fulfilled.
- **T024** — No `ridge_logS.pkl` or `ridge_logP.pkl` files, nor any JSON/report containing RMSE and Pearson r values, are present. Consequently the required calculation of metrics on the test set and saving of the model artifacts has not been demonstrated.
- **T027** — declared artifact(s) missing/empty/invalid: results/reports/sensitivity_sweep.json
- **T026** — declared artifact(s) missing/empty/invalid: results/reports/metrics.json
