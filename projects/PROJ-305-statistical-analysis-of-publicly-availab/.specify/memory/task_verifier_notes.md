# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Checked `src/data/download.py` (uses dataset `chrisvoncsefalvay/vaers-outcomes` instead of the required `"vaers/vaers2020_2023"`), the generated `data/raw/vaers_2020_2023.parquet` (size > 0) and `data/checksums.txt` (checksum line present). The wrong dataset source violates the task specification, so the requirement is not fully satisfied.
- **T003** — Requested task execution failed; rerun successfully: src/data/validate_raw.py exit=1
- **T004** — Requested task execution failed; rerun successfully: src/data/clean.py exit=1
