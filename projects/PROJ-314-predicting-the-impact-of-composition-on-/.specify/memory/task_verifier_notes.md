# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017b** — The repository contains a `generate_data_availability_report` function that writes the required JSON, but the `data/reports/data_availability_report.json` file is absent, indicating the report was never actually generated. Additionally, the function is called with a placeholder `total_sources=0`, which may not meet the intended semantics. The required output file is missing, so the task is not fully satisfied.
- **T025** — The integration test file exists, but the required output `data/results/cv_split_report.json` is absent, indicating the test either does not generate the report or has not been executed. The missing JSON report means the task’s core requirement is not satisfied.
- **T028b** — The provided `code/modeling.py` excerpt does not contain a `run_baseline_predictor()` implementation, and the required output file `data/results/baseline_metrics.json` is absent. Consequently the task’s core requirement—creating the baseline predictor and saving its MAE—is not satisfied.
- **T041** — declared artifact(s) missing/empty/invalid: data/results/shap_summary.png, data/results/feature_ranking_table.csv, data/results/stability_metrics.json
