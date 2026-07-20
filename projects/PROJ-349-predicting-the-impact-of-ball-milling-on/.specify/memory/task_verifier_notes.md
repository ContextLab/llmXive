# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or placeholder files were presented; without concrete evidence that the required folders (`src/`, `tests/`, `data/raw`, `data/processed`, `data/splits`, `results`, `contracts/`, `.github/workflows/`) exist, the claim cannot be verified. The implementer must provide a listing or screenshots showing these directories (and any placeholder files) in the repository.
- **T003** — No evidence of `flake8 --version`, `black --version`, or a successful `black --check src/` run is present; the required artifacts (version outputs and linting check results) are missing, so the linting configuration cannot be confirmed as completed.
- **T004** — No directory listings or filesystem evidence were provided; the required `data/raw`, `data/processed`, `data/splits`, and `results` folders are not shown to exist, so the task’s deliverable cannot be verified.
- **T013** — declared artifact(s) missing/empty/invalid: src/ingest/nist_repo.py, data/raw/nist_milling_data.csv, schema.yaml
- **T013b** — The repository contains `src/ingest/arxiv_extractor.py`, but the file is truncated and lacks any logic that extracts tables, writes them to `data/raw/arxiv_tables.json`, or raises `DataIngestionError` on failure. Moreover, the required output file `data/raw/arxiv_tables.json` does not exist. Consequently the task’s core requirements are not met.
