# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T078** — The required files `data/processed/step_final_cleaned.csv` and `data/reports/final_report.md` are missing, and the existing `model_metrics.json` is unrelated to the dry‑run (it references task T031 and predates the project). No dry‑run logs or evidence of the pipeline execution are provided.
- **T079** — declared artifact(s) missing/empty/invalid: data/raw/test_n.csv, data/reports/data_availability_report.json
- **T081** — declared artifact(s) missing/empty/invalid: data/results/correlated_clusters.json
- **T082** — declared artifact(s) missing/empty/invalid: data/results/stability_metrics.json
- **T083** — The required artifact `data/results/descriptor_sufficiency.json` is missing, so the pipeline was not run and no verification of the descriptor sufficiency logic could be performed. The task therefore lacks the essential output file.
- **T084** — The required artifact `data/results/permutation_test_report.json` does not exist, so there is no p-value, MAE improvement percentage, or significance flag to verify. The task cannot be considered completed until this file is generated with the appropriate contents.
- **T085** — declared artifact(s) missing/empty/invalid: data/reports/final_report.md
- **T086** — The required state file `state/projects/PROJ-314-predicting-the-impact-of-composition-on-.yaml` does not exist, so no artifact hashes can be verified. The implementer must ensure the script creates/updates this file with the expected `artifact_hashes` entries.
- **T087** — No memory‑profiler output, logs, or benchmark data were supplied to show that `fetch_materials_project_data_streaming()` was run on a large dataset and kept memory usage below 2 GB. The required artifact (e.g., a profiling report or screenshots) is missing, so the verification task is not satisfied.
