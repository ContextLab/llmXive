# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/`, `data/`, `contracts/`, or `tests/` directories is provided; the claim lacks any artifact confirming the directory structure was created.
- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015b** — The repository contains `code/preprocess/structural.py`, but the visible portion only defines `calculate_graph_metrics` and does not show any loop over `DENSITY_THRESHOLD_VARIATIONS` or code that writes a CSV file. Moreover, the required output file `data/processed/structural_density_sensitivity.csv` is absent. Hence the mandated sensitivity analysis and its result file are not present.
- **T017** — The provided `code/preprocess/functional.py` is truncated and never loads `data/processed/loo_centroids_all_subjects.npz` nor implements the per‑subject state‑assignment logic described. Moreover, the required `data/processed/loo_centroids_all_subjects.npz` file is absent. Both the code artifact and the data artifact needed for the task are missing/incomplete.
- **T019** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_log.json
- **T018** — The required output files `data/processed/structural_metrics.csv` and `data/processed/dynamic_metrics.csv` are absent, and the referenced `contracts/output.schema.yaml` (schema.yaml) is also missing. Consequently the batch aggregation logic cannot be verified as implemented.
- **T019b** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_log.json, data/processed/structural_metrics.csv, data/processed/completeness_report.json
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T028** — No code, test, or documentation artifact was provided showing that the pipeline now checks for zero significant findings after FDR correction and explicitly writes a statement to the report. Without a concrete implementation or evidence (e.g., updated script, unit test, or example report), the requirement is not satisfied. The next implementer must add the edge‑case handling logic, a test confirming the behavior, and an example output demonstrating the explicit statement.
- **T031** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_comparison.csv
