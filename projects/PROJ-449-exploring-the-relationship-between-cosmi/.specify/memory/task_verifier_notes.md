# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T056** — The required output `data/processed/bootstrap_block_sensitivity.json` does not exist, and the provided `bootstrap.py` snippet shows only data loading and a single bootstrap function—there is no evidence of a block‑size sensitivity loop, CI comparison, warning logic, or saving of results. The task’s core requirement is therefore unmet.
- **T057** — The provided `correlation.py` snippet shows no implementation of counting valid points per rigidity bin, skipping bins with < 100 points, or adding a `valid_data_points` column, and the required `data/processed/correlation_summary.csv` file is absent. Both the code changes and the output artifact required by the task are missing.
