# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T028a** — The required output file `results/simulation_results.csv` does not exist, and the provided `code/main.py` excerpt stops mid‑function without showing a full iteration loop, CSV writing, or the time‑limit/exit‑code logic. Consequently the deliverable specified in the task is not present.
- **T029** — The `calculate_aggregate_metrics` function in `code/analysis/metrics.py` is truncated and ends with an invalid return (`pd.DataF`), so the required aggregation logic is not implemented. Additionally, the required output file `results/aggregate_metrics.csv` and its prerequisite `results/simulation_results.csv` are missing from the repository.
- **T057** — The provided `metrics.py` does not contain a `run_sensitivity_analysis` implementation (the file ends abruptly with a typo in `calculate_aggregate_metrics`), and the required output file `results/sensitivity_analysis.csv` is absent. Both the function and the CSV result are needed to satisfy the task.
