# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The provided `code/main.py` is truncated (ends mid‑line with `run_coverage_with_cata`) and does not contain a complete batch‑processing routine (e.g., loading the catalog, iterating over all tasks, invoking `process_single_task` for each, and summarising results). Consequently the required orchestration logic is missing. The next implementer must supply the full script, ensuring it loops over the task catalog, generates code for each task, runs coverage, saves per‑task JSON reports, and handles errors as specified.
- **T029** — The required output file `data/processed/sensitivity_report.csv` does not exist, so the sensitivity analysis across the specified thresholds has not been produced. The task therefore remains unfinished.
