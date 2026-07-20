# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or screenshots were provided showing that the required folders (`code/ingestion`, `code/features`, `code/modeling`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs`) actually exist in the repository. Without concrete evidence of these paths being created, the task requirement is not satisfied.
- **T003** — The `code/.ruff.toml` file exists and contains the correct linting rules and line‑length setting, but there is no evidence that the `ruff` package was actually installed (e.g., no `requirements.txt`, `pyproject.toml`, or lock file showing `ruff` as a dependency). The installation step is missing.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The integration test file does not contain a `test_schema_validation` function that checks the DataFrame columns against a schema, and the required `contracts/mg_dataset.schema.yaml` file is absent from the repository. Both the specific test and the schema artifact are missing, so the task is not satisfied.
- **T013** — No `fetch_data.py` file is present in `code/ingestion/`, and therefore there is no implementation that queries the Materials Project and AFLOWlib APIs or collects the required entries. The required artifact is missing.
- **T016** — No `descriptors.py` file (or its contents) is present in `code/features/`, and no code implementing the weighted mean atomic radius, electronegativity variance, VEC, or atomic size mismatch calculations is provided. The required artifact is missing, so the task is not satisfied.
- **T017a** — The `code/features/descriptors.py` file shown contains no comment explaining why `size_mismatch` is kept despite a high VIF, and the required `results/metrics.json` file does not exist at all. Both the documentation comment and the JSON flag for VIF > 5.0 are missing.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/clean_mg_data.parquet
