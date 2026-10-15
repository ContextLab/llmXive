# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows the `data/`, `models/`, `reports/`, `src/pipeline/` and `src/cli/` directories, a seeded run, and a dry‑run command that creates `data/results/sample_run.csv` (4 rows). However, the required `interim/` and `features/` directories are not present, and `quickstart.md` contains multiple command blocks rather than the single `python -m src.cli.run_pipeline --dry-run` command stipulated. These omissions mean the task is not fully satisfied.
- **T002** — Requested task execution failed; rerun successfully: src/pipeline/ingest.py exit=1
