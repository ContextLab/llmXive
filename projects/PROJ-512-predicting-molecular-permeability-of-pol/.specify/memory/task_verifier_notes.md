# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `pyproject.toml` file is present, but the required `.ruff.toml` file does not exist, so the deliverable of providing both configuration files is not satisfied. The missing `.ruff.toml` must be added with explicit Ruff settings.
- **T010** — The `ingestion.py` script does not save raw data checksums to `raw/checksums.json` (the file is missing) and the `main` function is truncated, leaving no real NIST/PubChem URL or logic to download actual data. Moreover, only the “< 500 records” case raises the required `DataUnavailableError` message; other failure modes (e.g., 404) raise a different message. The task’s core requirements are therefore not met.
