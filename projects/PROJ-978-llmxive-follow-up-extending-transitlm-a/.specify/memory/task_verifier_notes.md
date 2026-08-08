# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory tree (`code/`, `data/raw/`, `data/processed/`, `data/analysis/`, `models/`, `analysis/`, `tests/`, `docs/`) is provided; the artifacts are missing, so the task is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` or `.ruff.toml` for ruff, and black settings or a pre‑commit hook) are present in the provided artifacts, and the evidence only describes a research feature spec unrelated to configuring ruff/black. The required linting/formatting setup is missing.
- **T004** — The provided `data/download.py` is truncated, never invokes the SHA256 check, and writes to `transitlm_sft_raw.jsonl` instead of the required `transitlm_ground_truth.json`. Moreover, the expected output file `data/raw/transitlm_ground_truth.json` is missing.
- **T006a** — declared artifact(s) missing/empty/invalid: data/preprocess.py, data/processed/city_filtered_routes.jsonl
- **T006b** — declared artifact(s) missing/empty/invalid: data/preprocess.py, data/processed/vocab_restricted_routes.jsonl
- **T006c** — declared artifact(s) missing/empty/invalid: data/preprocess.py, data/processed/stratified_routes.parquet
