# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The provided `code/preprocess.py` is truncated and only contains parsing utilities; it does not show any implementation of gene annotation with pybedtools nor aggregation of peaks into a background model, nor does it write `data/interim/background_union.bed`. Moreover, the required output file `background_union.bed` is missing from the repository. The task’s core requirements are therefore not satisfied.
- **T015** — The repository contains a `code/main.py` file, but the `run_ingestion` function is truncated and does not show the logic that writes `data/processed/ingestion_summary.json`. Moreover, the required `data/processed/ingestion_summary.json` file is absent. The task’s core output is therefore missing.
