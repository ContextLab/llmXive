# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — the task writes platform-owned path(s) inside the project: `.github/workflows/research.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T005** — The `code/utils.py` module exists and implements the requested functions, but the required output file `results/monitoring.csv` was not created – it is listed as MISSING, so the self‑test did not generate the CSV with the header and a row. The task’s verification step (checking the CSV contents) cannot be satisfied until this file is produced.
- **T006** — The repository contains `data/manifest.json` and the data‑gap resolver script, but no `Snakefile` (or any Snakemake workflow) is present. Consequently the required `verify_data_availability` rule, its dependency on `download`, and the minimal `data_gap_resolver` rule are missing. Adding a correctly‑named Snakefile with those rules is needed to satisfy the task.
- **T007** — Requested task execution failed; rerun successfully: code/data_gap_resolver.py exit=1
- **T008** — Requested task execution failed; rerun successfully: code/preprocess_and_geometry.py exit=1
