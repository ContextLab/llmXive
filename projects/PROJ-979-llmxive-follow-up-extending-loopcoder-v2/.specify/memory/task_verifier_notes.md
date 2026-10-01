# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012a** — declared artifact(s) missing/empty/invalid: data/processed/filtered_splits.json, data/processed/exclusion_log.json, data/processed/entropy_results.csv
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/convergence_results_sensitivity.csv
- **T035** — The required input file `data/processed/filtered_splits.json` does not exist, and the expected output `data/processed/entropy_results.csv` is also missing; there is no evidence that the script was run, that it exited with code 0, or that it produced the output file. The task therefore remains unfinished.
- **T036** — The required input `data/processed/filtered_splits.json` and the expected output `data/processed/convergence_results_core.csv` are both absent, and there is no evidence (e.g., logs, exit‑code capture) that the inference script was actually executed. The task therefore has not been fulfilled.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/router_model.pkl, data/processed/router_metrics.json
- **T019c** — declared artifact(s) missing/empty/invalid: data/processed/router_cv_folds.json
- **T019b** — No `router_results.csv` file or any other output was presented; the conversation contains only the task description and no evidence of the router being applied to the test set or of a CSV with the required columns (`task_id, predicted_k, actual_k, accuracy, is_censored`). The required artifact is missing.
- **T020a** — No `static_k2_baseline.json` file containing `{total_flops, accuracy}` was provided, nor any FLOPs or accuracy numbers for the always‑k=2 baseline on the filtered test set. Consequently the required artifact is missing.
- **T021c** — The required `data/processed/config.json` file is missing, so the extracted `NON_INFERIORITY_DELTA` and `RANDOM_SEED` have not been written to the expected location. The implementer must create the JSON file containing those two values.
- **T025a** — No `stratum_pvalues_powered.json` file or any other output artifact was presented. Without the required JSON containing the per‑stratum powered‑only p‑values, the task’s deliverable is missing. The implementer must generate and provide this file.
- **T025c** — The claim provides no actual `convergence_results_merged.csv` file (or any CSV) to inspect, and there is no evidence that the two source CSVs were concatenated. Without the merged file present and verified, the task requirement is not satisfied.
- **T026** — No `sensitivity_sweep.json` file or any computed Spearman ρ results for thresholds k = 2, 3, 4 are present; the implementer provided only the task description and project spec without the required output artifact. Consequently, the task’s deliverable is missing.
- **T025f** — No `robustness_summary.json` file (or any combined output) is present; the implementer did not provide the required merged JSON artifact linking `adjusted_pvalues_powered.json` and `mixed_effects_results.json`. Consequently the task’s core requirement is unmet.
