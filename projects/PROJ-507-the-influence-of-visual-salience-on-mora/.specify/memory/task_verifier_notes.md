# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required output files are absent: `data/raw/checksums.json` and `data/processed/candidates_filtered.csv` do not exist, and `data/raw/` is empty, so there is no evidence that `code/01_ingest_and_filter.py` was run successfully or produced the mandated CSV rows and checksums. The unit test only checks a failure path and does not verify successful ingestion. The task therefore lacks the essential artifacts.
- **T002** — The repository lacks the required `data/raw/human_coding/` directory (marked MISSING), which the task explicitly demanded to be created. All other artifacts (the CLI script and passing unit tests) are present, but the missing folder means the requirement is not fully satisfied.
- **T003** — Requested task execution failed; rerun successfully: code/03_process_human_coding.py exit=1
