# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains the ingestion script and the raw CSV with a correct checksum, but the required output artifacts are absent: `data/processed/power_analysis_report.json`, `data/logs/large_molecule_exclusions.log`, `data/processed/scaffold_counts.json`, `data/processed/splits.json`, and `data/processed/filtered_esol.csv` are all missing. Without these files the power analysis, molecular‑weight exclusions, scaffold count check, split generation, and filtered dataset are not produced, so the task is not fully satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/02_tda_computation.py exit=1
