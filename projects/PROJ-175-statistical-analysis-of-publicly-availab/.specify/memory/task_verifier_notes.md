# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The repository contains `code/data/preprocess.py`, but it only builds a tiny hard‑coded canonical map and writes a placeholder JSON (`canonical_map_size` etc.) to a path derived from `processed_dir.parent`, not to the required `data/normalization_config.json` (which is missing). No actual mapping or exclusion counts are logged, and the script does not process real Recipe1M ingredient data. The required output file is absent, so the normalization step is not genuinely implemented.
- **T008** — The `data/power_analysis.json` file exists and contains the required fields, but the required second artifact `data/split_config.json` is missing, so the task’s deliverables are not fully satisfied.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/co_occurrence_matrix.parquet
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/flavor_similarity.parquet
- **T019** — declared artifact(s) missing/empty/invalid: data/split_config.json
- **T040b** — The required artifact `data/final/logistic_results.json` does not exist, so the logistic regression re‑fit after predictor drop has not been recorded as required. The task therefore remains unfinished.
- **T022** — Both required artifacts are absent: `data/final_predictors.json` (the predictor list) and `data/final/logistic_results.json` (the logistic regression results) do not exist on disk, so the model fitting cannot have been performed. The task therefore is not satisfied.
- **T025** — The required output file `data/final/bayesian_results.json` is missing, so the core artifact of the task was not produced. The convergence log exists, but without the results JSON the task’s primary requirement is unmet.
- **T047** — declared artifact(s) missing/empty/invalid: data/vif_test_set.json
- **T029** — declared artifact(s) missing/empty/invalid: data/evaluation_metrics.json
- **T099** — declared artifact(s) missing/empty/invalid: code/run_full_pipeline.py
- **T043a** — declared artifact(s) missing/empty/invalid: data/pipeline_execution_log.json
