# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The `download_gsm8k.py` file is present but only a partial snippet is shown, ending abruptly before the dataset loading and saving logic, so we cannot confirm it actually downloads, filters, asserts >200 valid examples, and writes `data/raw/gsm8k_verified.parquet`. Moreover, the required parquet file does not exist. The implementation needs to be completed and verified.
- **T014** — No code or test output was provided showing that `generate_oracle.py` now computes the variance of the output coefficients and aborts when the variance ≤ 1e‑9. The required artifact (the updated script with the explicit variance validation) is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/delta_coefficients.json, schema.yaml
- **T018** — The required output file `data/processed/static_features.parquet` is absent, and the provided `extract_features.py` script is incomplete (truncated) and does not demonstrate that it writes the specified parquet with the required columns. The task’s primary deliverable is therefore not satisfied.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/static_features.parquet, schema.yaml
- **T022** — The `code/models/train.py` script exists, but the required output model file `data/processed/mlp_model.pt` is missing, so the implementation does not fulfill the task’s requirement to save the trained model.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/predictions.json
- **T026b** — declared artifact(s) missing/empty/invalid: code/eval/metrics.py
