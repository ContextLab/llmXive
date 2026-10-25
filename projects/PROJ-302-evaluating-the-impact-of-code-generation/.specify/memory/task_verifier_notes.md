# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `data/raw/` directory contains only a `.gitkeep`; no `<owner>_<repo>.parquet` files or `commit_messages.parquet` were generated, and the required `pull_request.schema.yaml` is absent. Consequently the task’s core deliverables (parquet files with PR rows and the schema) are missing.
- **T003** — The repository contains `code/prompt_engineering.py`, but the required input file `data/raw/commit_messages.parquet` is missing, causing the script (and its unit test) to fail, and consequently `data/processed/intent_prompts.parquet` is never created. Both the source parquet and the output parquet must exist for the task to be satisfied.
- **T004** — Requested task execution failed; rerun successfully: code/synthetic_generation.py exit=1
