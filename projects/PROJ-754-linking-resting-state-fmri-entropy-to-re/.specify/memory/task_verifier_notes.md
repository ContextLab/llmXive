# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/src/run_pipeline.py exit=1
- **T002** — Requested task execution failed; rerun successfully: code/src/data/download_hcp.py exit=1
- **T003** — The `code/src/data/qc.py` script is present and implements the required logic, but the essential input file `data/raw/dsrt_scores.parquet` is missing, and consequently the required output artifacts `data/derived/clean_subjects.parquet` and `data/derived/subject_qc.csv` were not generated or provided. Without the input data and the resulting QC files, the task’s verification conditions cannot be satisfied.
- **T004** — Requested task execution failed; rerun successfully: code/src/analysis/entropy.py exit=1
