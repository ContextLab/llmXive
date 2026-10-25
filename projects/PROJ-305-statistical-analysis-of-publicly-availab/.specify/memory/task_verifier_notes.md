# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `src/data/download.py` script does not use the required dataset identifier `datasets.load_dataset("vaers/vaers2020_2023", split="train")`; it instead loads `"chrisvoncsefalvay/vaers-outcomes"`. Consequently the implementation does not meet the task’s primary specification, even though the parquet file and checksum line exist. The script must be updated to load the exact `vaers/vaers2020_2023` dataset.
- **T003** — Requested task execution failed; rerun successfully: src/data/validate_raw.py exit=1
- **T004** — Requested task execution failed; rerun successfully: src/data/clean.py exit=1
