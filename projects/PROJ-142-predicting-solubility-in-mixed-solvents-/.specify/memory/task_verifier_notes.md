# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — declared artifact(s) missing/empty/invalid: tests/contract/test_schema_validation.py
- **T010** — declared artifact(s) missing/empty/invalid: tests/integration/test_pipeline.py
- **T012** — The `data/processed/cleaned_compositions.csv` file does not exist, and the shown portion of `code/01_data_ingestion.py` is truncated before any logic that normalizes/rejects compositions and writes the filtered DataFrame to that path. Consequently, the required validation and output generation are not demonstrably implemented.
- **T013** — The required log file `data/artifacts/imputation_log.txt` does not exist, and the provided excerpt of `code/01_data_ingestion.py` shows no implementation of KNN imputation, row‑dropping on failure, or logging of the imputation rate. The task’s core functionality and artifact are missing.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/solubility_features.csv
- **T020** — declared artifact(s) missing/empty/invalid: tests/integration/test_training.py
- **T023** — The required artifact `data/artifacts/trained_models.pkl` does not exist, so the evaluation script cannot load any models. Moreover, the provided `code/04_evaluation.py` is truncated and does not show logic that iterates over all loaded models to compute RMSE, MAE, and R². Both the missing model file and the incomplete script prevent the task from being fulfilled.
- **T024** — The required artifact `data/artifacts/trained_models.pkl` does not exist, and the output file `data/artifacts/statistical_test_results.json` is also missing. Moreover, the provided `code/04_evaluation.py` does not contain a paired t‑test on absolute errors nor code to write the p‑value and t‑statistic to the JSON file. These core components must be added for the task to be considered complete.
- **T024b** — declared artifact(s) missing/empty/invalid: data/artifacts/training_report.json
- **T025** — declared artifact(s) missing/empty/invalid: data/artifacts/training_report.json
