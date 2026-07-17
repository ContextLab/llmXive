# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listings or file system evidence were provided showing that the required folders (`code/data`, `code/models`, `code/eval`, `data/raw`, `data/processed`, `contracts`) actually exist; the response contains only the task description and specifications. The implementer must create and demonstrate the presence of these directories.
- **T001b** — No evidence was provided showing that the `code/`, `data/`, and `tests/` directories exist or contain the required `__init__.py` and `.gitkeep` files; without these artifacts the initialization task cannot be confirmed as done.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `ruff.toml` or `.ruff.toml`, or CI scripts invoking ruff/black) are present, nor any documentation showing they have been set up. The required artifacts to prove that linting (ruff) and formatting (black) are configured are missing.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The provided `download_gsm8k.py` is truncated (the `verify_solution_correctness` function ends mid‑line and no code to download, filter, or write the Parquet file is present), and the required `data/raw/gsm8k_verified.parquet` file does not exist. Consequently the task’s core requirements are not satisfied.
- **T015** — The `data/processed/delta_coefficients.json` file exists but the required schema file `contracts/delta_oracle.schema.yaml` is missing, so conformance cannot be verified. Moreover, the JSON contains only a handful of token entries rather than the full set of coefficients for the 500‑example GSM8K subset required by the specification. The task is therefore not satisfied.
- **T018** — The required output file `data/processed/static_features.parquet` does not exist, and the provided `extract_features.py` script is incomplete (truncated) with no visible logic that writes the required parquet with columns `[token_id, feature_vector]`. The task’s core deliverable is therefore missing.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/static_features.json, schema.yaml
- **T022** — The provided `code/models/train.py` is truncated and does not show a complete training loop, nor any code that saves the trained model to `data/processed/mlp_model.pt`. Additionally, the expected output file `mlp_model.pt` is missing. The implementation must include the full training procedure, enforce CPU‑only execution, and write the model checkpoint to the specified path.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/predictions.json
