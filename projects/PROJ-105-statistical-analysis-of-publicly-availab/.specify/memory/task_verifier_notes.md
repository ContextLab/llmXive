# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required raw archive `data/raw/2022/On_Time_Reporting_CSV.zip` is missing, and `data/README.md` (which should contain the checksum) is also absent. The provided `code/data_loader.py` attempts to download from a URL that returns 404, causing the test `test_download_creates_zip` to fail and no zip file is created. Consequently the task’s core requirement—streaming download of the full‑year 2022 CSV and storing it as a ZIP archive—is not satisfied.
- **T002** — The required implementation file `code/preprocess.py`, the output dataset `data/processed/cleaned_delays.csv`, and the schema file `delay_record.schema.yaml` are all missing from the project, so the task’s core deliverables are not present.
- **T003** — Requested task execution failed; rerun successfully: code/t003_summary.py exit=1
