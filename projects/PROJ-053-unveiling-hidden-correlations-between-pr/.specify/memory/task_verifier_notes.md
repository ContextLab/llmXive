# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `requirements.txt` and `code/utils/io_utils.py` exist and correctly set seeds (42 via config), but the task's verification requirements are unmet: there is no evidence of a virtual environment setup, no `pip freeze` output matching pinned versions, and no test script confirming seed consistency across runs. The implementer must provide a seed-consistency test script (with execution evidence) and a `pip freeze`/environment record.
- **T002** — Requested task execution failed; rerun successfully: code/data_loader.py exit=1
- **T003** — The required files `code/preprocessing.py`, `data/processed/train.csv`, `data/processed/test.csv`, and `data/processed/preprocessing.log` are all missing, and the provided test `tests/test_preprocessing.py` fails because no raw CSV is found, so the preprocessing pipeline never produces the expected outputs.
- **T004** — The required model scripts (`code/models/gpr_model.py`, `code/models/baseline.py`) and the saved model artifacts (`results/model/gpr_model.joblib` and `baseline_model.joblib`) are absent, and the metrics JSON does not contain the exact key `rmse_percentage_range` (it has `rmse_percentage_of_range` instead). These missing/incorrect artifacts prevent the task from being considered complete.
- **T005** — Requested task execution failed; rerun successfully: code/analysis/importance.py exit=1
