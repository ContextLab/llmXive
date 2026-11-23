# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/data/download.py exit=1; code/data/preprocess.py exit=1
- **T002** — Checked `code/data/preprocess.py` (implements all required steps) and `data/processed/filtered.csv` (contains rows that conform to `contracts/dataset.schema.yaml`). However, the required log file `logs/preprocess_summary.log` is not present in the provided artifacts, so the task’s verification requirement is not satisfied. Adding this summary log (with total, filtered, and excluded row counts) is needed to complete the task.
- **T003** — Requested task execution failed; rerun successfully: code/data/split.py exit=1
