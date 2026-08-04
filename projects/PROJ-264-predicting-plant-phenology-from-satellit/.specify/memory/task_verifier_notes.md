# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No code, data files, model artifacts, or performance reports were provided; the claim references an unspecified placeholder and there is no concrete evidence that the ingestion pipeline, model training, or sensitivity analysis were implemented or executed. The required deliverables are missing.
- **T003** — The claim provides no visible configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `black` config) or any script/command showing that ruff linting and black formatting have been set up for the project. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied. The next implementer should add the appropriate configuration files and ensure they are non‑empty and correctly reference ruff and black.
- **T004** — declared artifact(s) missing/empty/invalid: src/config.py
- **T006** — No `tests/contract/` directory, pytest‑jsonschema configuration, or validation scripts are present, and there is no generated artifact linking `config.py` to `contracts/config_schema.json` or updating `data-model.md`. Consequently the required testing framework and documentation output are missing.
- **T008** — No directory hierarchy under `data/raw/` or `data/processed/` and no checksum scripts are provided in the evidence; the implementer did not supply any files or code to demonstrate the required structure or functionality.
