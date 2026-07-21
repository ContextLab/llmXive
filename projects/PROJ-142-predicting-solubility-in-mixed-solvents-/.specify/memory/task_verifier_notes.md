# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — declared artifact(s) missing/empty/invalid: tests/contract/test_schema_validation.py
- **T010** — declared artifact(s) missing/empty/invalid: tests/integration/test_pipeline.py
- **T011** — declared artifact(s) missing/empty/invalid: code/01_data_ingestion.py
- **T012** — declared artifact(s) missing/empty/invalid: code/01_data_ingestion.py, data/processed/cleaned_compositions.csv
- **T013** — The required source file `code/01_data_ingestion.py` and the log file `data/artifacts/imputation_log.txt` are both missing, so no KNN imputation implementation, row‑dropping logic, or logging of the imputation rate is present. The task’s deliverables are absent.
- **T016** — The provided `code/02_feature_engineering.py` does not show any implementation of explicit interaction term generation (polynomial or ratio), and the file is truncated before any such logic could appear. Moreover, the required output file `data/processed/solubility_features.csv` is absent, so no new columns have been appended. The task is therefore not fulfilled.
- **T017b** — The required file `data/artifacts/pivot_decision.json` does not exist, so the condition to trigger the task cannot be evaluated, and there is no evidence that `tasks.md` was updated accordingly. Both the pivot decision artifact and the updated task definitions are missing.
- **T017c** — The required artifact `data/artifacts/pivot_decision.json` is missing, and there is no evidence that `tasks.md` was updated to reflect a pivot decision. Consequently the verification step cannot be performed as specified.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/solubility_features.csv
- **T020** — declared artifact(s) missing/empty/invalid: tests/integration/test_training.py
- **T023** — The required `data/artifacts/trained_models.pkl` file does not exist, so the evaluation script cannot load any models. Moreover, `code/04_evaluation.py` is incomplete (syntax errors, truncated logic, missing implementation of metric calculations). Both the necessary artifact and a functional evaluation implementation are absent.
