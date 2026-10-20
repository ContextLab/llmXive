# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `requirements.txt`, which correctly pins the listed packages to the `major.minor.*` pattern, but there is no provided evidence (e.g., install logs or CI regex check output) that `pip install -r requirements.txt` actually succeeds on a clean runner or that the CI regex validation was performed. These execution confirmations are required to complete the task.
- **T003** — Requested task execution failed; rerun successfully: code/ingestion/run_download_real.py exit=1
- **T004** — The repository lacks the required output artifacts `data/processed/aligned_hourly.parquet` and `data/artifacts/alignment_report.json`; they are marked MISSING. Consequently the task’s core deliverables are not present despite the implementation and unit test existing. Generating these files at the specified locations (and ensuring they meet the schema and gap‑flagging requirements) is needed to complete the task.
- **T005** — Requested task execution failed; rerun successfully: code/analysis/coupling_functions.py exit=1
