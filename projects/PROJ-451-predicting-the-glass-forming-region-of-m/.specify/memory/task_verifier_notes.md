# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or corresponding entry‑point scripts) are present in the provided evidence, so the requirement to configure ruff and Black has not been satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- **T006** — No `.env.example` file or `utils/config.py` module was presented in the evidence, and thus there is no proof that the required placeholders and validation logic exist. The implementer must supply these two files with the specified contents.
- **T010a** — declared artifact(s) missing/empty/invalid: scripts/ingest_zenodo.py
- **T010b** — declared artifact(s) missing/empty/invalid: scripts/ingest_mp.py
- **T010c** — The repository lacks the required `scripts/ingest.py` file (the core merge/validation logic) and does not contain a `provenance.json` with per‑record source metadata. Without these artifacts the task’s specifications are not met.
- **T017a** — The required `scripts/ingest.py` file does not exist, and the expected output `data/processed/filtered_properties.csv` is also missing, so the property‑filtering step has not been implemented nor any results produced.
- **T017b** — declared artifact(s) missing/empty/invalid: data/processed/completeness_check.json
- **T019** — No `features/alloy_system_mapper.py` file or its contents are provided, so we cannot confirm that a non‑empty implementation exists, that it follows the specified mapping logic, or that it adds an `alloy_system` column to the dataset. The required artifact is missing.
- **T014** — declared artifact(s) missing/empty/invalid: scripts/ingest.py
