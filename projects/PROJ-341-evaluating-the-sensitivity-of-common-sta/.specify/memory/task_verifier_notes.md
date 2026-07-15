# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The required file `data/simulation_metadata.json` does not exist in the repository, so no schema was provided for storing seeds, configuration, and timestamps. The implementer must add this JSON file with the appropriate schema.
- **T014b** — The provided `code/main.py` file is present, but the excerpt stops before the body of `run_simulation`; the actual loop over sample sizes, effect sizes, and hypotheses (and the enforcement of the iteration constraint) is not shown, so we cannot confirm the required parameter‑loop logic was implemented. The missing implementation must be added or displayed to satisfy the task.
- **T016** — The required file `data/simulation/p_values_raw.csv` does not exist, so no output containing the specified columns (sample size, effect size, test type, raw p-values, hypothesis state) is present. The task’s core deliverable is missing.
- **T018** — The required file `data/simulation/error_rates_summary.csv` does not exist, so the aggregated error rates were not saved as specified. The task’s core deliverable is missing.
