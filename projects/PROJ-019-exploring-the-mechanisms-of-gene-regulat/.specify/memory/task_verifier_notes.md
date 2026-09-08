# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The required output file `data/interim/background_union.bed` is not present, and the provided `code/preprocess.py` snippet is incomplete (truncated) with no visible logic that performs gene annotation, background aggregation, or writes the specified BED file. The task’s core deliverable is therefore missing.
- **T015** — The repository contains `code/main.py` with a `run_ingestion` function that validates cell types and computes summary values, but the function only returns a dictionary and never writes `data/processed/ingestion_summary.json`. The required output file is absent from the project tree, so the task’s primary artifact is missing.
