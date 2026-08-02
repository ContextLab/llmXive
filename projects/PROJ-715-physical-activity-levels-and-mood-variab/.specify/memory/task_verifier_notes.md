# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `setup.cfg`, `pyproject.toml` with Black settings) or related scripts were presented for the `code/` directory, and there is no evidence that flake8 and Black have been set up or integrated. The implementer must add the appropriate configuration files and ensure they are applied to the codebase.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — The provided `code/ingest.py` contains placeholder URL and checksum values, does not retrieve the DOI from the config, and the script is incomplete/truncated (missing the end of `main`). Moreover, the required output file `data/raw/bronze.parquet` is not present. The implementation therefore does not fulfill the download‑verify‑convert requirement.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/daily_aggregates.csv, schema.yaml
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json, schema.yaml
