# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T029a** — declared artifact(s) missing/empty/invalid: data/analysis/simulation_results.json
- **T029** — declared artifact(s) missing/empty/invalid: data/analysis/simulation_results.json
- **T035b** — The required `data/analysis/sensitivity_sweep.json` file does not exist, and the provided `sensitivity.py` does not implement saving the sweep results nor ensure ≥5 distinct thresholds. Moreover, the unit test expects function signatures (e.g., `filter_by_clustering_threshold(df, 0.5, '>=')`) that are not present in the implementation, so the test would fail. The task’s core requirements are therefore unmet.
- **T037** — The `run_analysis.py` script exists, but the required output file `data/analysis/final_results.json` is missing, and the provided code excerpt does not show the aggregation (mean/median/variance), execution of the specified tests, or the saving of results in the required schema. Without the final JSON file and confirmed implementation of those steps, the task is not genuinely completed.
- **T044** — The provided `power.py` is only partially shown and does not contain any code that writes the required `power_analysis_report.json` with the specified schema. Moreover, the expected output file `data/analysis/power_analysis_report.json` is absent from the repository. The task therefore remains unfinished.
- **T045a** — The repository lacks the required `data/analysis/sensitivity_sweep.json` file, so SC‑005 cannot be validated, and the provided `validate_batch.py` snippet ends abruptly without showing any logic for SC‑005 (or a complete implementation of SC‑002). Consequently the batch validation logic does not fully meet the task’s specifications.
- **T045b** — declared artifact(s) missing/empty/invalid: data/analysis/validation_report.json
