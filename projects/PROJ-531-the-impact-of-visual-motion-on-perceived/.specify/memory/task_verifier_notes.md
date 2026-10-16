# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Checked `code/download_data.py` and the generated `data/raw/download_status.json`. The script never attempts to download a dataset or create `data/raw/real_data.parquet` (the file is missing), it always returns `instrument_valid = false` via a placeholder stub (no DOI, citation, or Cronbach’s α checks), and it exits with code 0 even when the instrument is invalid. Consequently the required dataset query, instrument validation, raw data saving, and error‑exit behavior are not implemented.
- **T002a** — Requested task execution failed; rerun successfully: code/check_instrument_validity.py exit=1
