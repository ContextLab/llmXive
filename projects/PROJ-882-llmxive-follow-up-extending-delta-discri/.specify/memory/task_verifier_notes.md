# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The provided `download_gsm8k.py` is truncated (e.g., the `verify_solution_correctness` function ends mid‑line) and contains no logic to actually download the dataset, filter examples, assert >200 valid entries, or write a Parquet file. Moreover, the required output file `data/raw/gsm8k_verified.parquet` does not exist. The task therefore remains unfinished.
- **T014** — No code or test output was provided showing that `generate_oracle.py` now computes the variance of the output coefficients and aborts when the variance ≤ 1e‑9. The required artifact (the updated script with the explicit variance validation) is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/delta_coefficients.json, schema.yaml
- **T018** — The repository contains `code/data/extract_features.py`, but the file is truncated and does not clearly implement selection of the first 50 GSM8K examples, n‑gram/POS extraction per token, or writing a Parquet file with columns `[token_id, feature_vector]`. Moreover, the required output `data/processed/static_features.parquet` is absent. The missing output file and incomplete script mean the task’s requirements are not met.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/static_features.parquet, schema.yaml
- **T022** — The `code/models/train.py` script exists, but the required output model file `data/processed/mlp_model.pt` is missing, so the implementation does not fulfill the task’s requirement to save the trained model.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/predictions.json
