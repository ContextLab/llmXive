# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listings or other evidence were supplied showing that the required folders (`code/`, `data/raw/`, `data/derived/`, `tests/`, `specs/`, `results/`, `docs/`) actually exist; the claim is unsubstantiated.
- **T001b** — No evidence of `.gitkeep` files in any data directories is provided; the artifact list is empty, so the requirement to create placeholder files in all data directories is not demonstrated. The implementer must add the `.gitkeep` files to each data folder and show their presence.
- **T003** — The `requirements.txt` and `pyproject.toml` files are present and populated, but the required `.pre-commit-config.yaml` file is missing entirely. The task is not fully satisfied until this configuration file is created.
- **T004** — No GitHub Actions workflow file (e.g., `.github/workflows/ci.yml`) or any description of its contents was provided, nor any evidence of checksum validation steps. The required CI configuration artifact is missing, so the task is not satisfied.
- **T010** — The required artifact `tests/integration/test_osf_client.py` does not exist on disk, so no integration test for the OSF API connection and backoff logic is present. The task cannot be considered fulfilled.
- **T011** — The JSON file `data/derived/study_records_raw.json` exists, but the required schema file `specs/contracts/study_record.schema.yaml` is missing, and there is no evidence that any schema validation was performed. Without the schema and a validation result, the contract test cannot be considered satisfied.
