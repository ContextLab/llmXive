# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or screenshots were provided showing that the required folders (`code/ingestion`, `code/features`, `code/modeling`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs`) actually exist in the repository. Without concrete evidence of these paths being created, the task requirement is not satisfied.
- **T003** — The `code/.ruff.toml` file exists and contains the correct linting and formatting rules, but there is no evidence that the `ruff` package was actually installed (e.g., no entry in `requirements.txt`, `pyproject.toml`, or installation script). The task’s “Install `ruff`” requirement is therefore unmet.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The integration test file exists but is truncated and never actually creates or validates a real DataFrame against the schema. Moreover, the required schema file `contracts/mg_dataset.schema.yaml` is missing, causing the test’s fixture to fail. Both the test implementation and the schema artifact need to be completed.
- **T013** — No `fetch_data.py` file is present in `code/ingestion/`, and therefore there is no implementation that queries the Materials Project and AFLOWlib APIs or collects the required entries. The required artifact is missing.
- **T016** — No `descriptors.py` file (or its contents) is present in `code/features/`, and no code implementing the weighted mean atomic radius, electronegativity variance, VEC, or atomic size mismatch calculations is provided. The required artifact is missing, so the task is not satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/clean_mg_data.parquet
- **T025** — No `train.py` file was presented in `code/modeling/`, nor any code snippet showing it loading `clean_mg_data.parquet` and constructing a feature matrix. Without the actual script, we cannot confirm the required artifact exists or meets the specification. The implementer must provide a non‑empty `train.py` that performs the described data loading and feature preparation.
- **T031** — No model files or metadata were found in a `models/` directory; the implementer provided no serialization artifacts, hyperparameter listings, or cross‑validation scores, so the required output is missing.
- **T034** — declared artifact(s) missing/empty/invalid: tests/integration/test_analysis.py
