# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No configuration files, scripts, or documentation for managing environment variables (e.g., `.env` files, `dotenv` setup, or path‑handling code) were provided. The claim does not include any artifact that shows API keys or data paths are configured, so the requirement is unmet.
- **T008** — No code, configuration files, or documentation for a base logging system (e.g., Python logging setup, log schema, provenance capture scripts) is present. The only artifacts described relate to data acquisition, modeling, and visualization, not to logging infrastructure, so the required artifact is missing.
- **T014** — declared artifact(s) missing/empty/invalid: code/preprocess.py
- **T015** — declared artifact(s) missing/empty/invalid: code/preprocess.py
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_data.csv
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_data.csv, data/processed/modeling_config.json
- **T016b** — The required artifact `data/processed/modeling_config.json` does not exist, so the code cannot read the `abort_flag` or enforce the N ≥ 80 gate as specified. The missing file must be provided (or generated) for the task to be satisfied.
- **T018** — No code, script, or documentation was presented that adds the required validation logic to filter out trait/personality measures from the primary regression while permitting them only as covariates in secondary checks. Without any artifact to inspect, the task’s specification has not been demonstrably fulfilled.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/modeling_config.json
- **T021b** — No code, notebook, script, or output files showing a Ridge Regression model with k‑fold cross‑validation are present, and there are no reported ridge coefficients or feature‑importance values. The required artifact is missing, so the task is not satisfied.
- **T022** — No code, notebook, script, or result files were provided that demonstrate performing statistical significance tests on ≥3 features with Bonferroni or Benjamini‑Hochberg correction. The required artifact (e.g., a reproducible analysis script and corrected p‑values) is missing, so the task is not satisfied.
- **T022b** — No code, data, or output files were supplied showing a fitted Random Forest model, k‑fold cross‑validation, feature importance scores, or out‑of‑sample R²/RMSE metrics. The required artifacts are missing, so the task is not satisfied.
- **T023** — declared artifact(s) missing/empty/invalid: code/sensitivity_analysis.py, data/results/sensitivity_analysis.csv
- **T024** — No code, data files, metric outputs, or feature‑importance map artifacts were provided; the claim cannot be verified because the required R², RMSE values and the FR‑004/SC‑002 importance visualizations are missing. The implementer must supply the computed out‑of‑sample metrics and the stored feature‑importance maps.
- **T025** — No output metadata artifact was provided, and there is no evidence that any reported associations have been labeled or framed as correlational. Without a concrete file (e.g., JSON, CSV, or report) showing the required framing, the task requirement cannot be confirmed as satisfied.
- **T026** — declared artifact(s) missing/empty/invalid: data/results/model_metrics.json
- **T029** — No code, script, or generated figure for a feature‑importance bar chart is present; the evidence provided contains only the specification text and no artifact that demonstrates the required visualization has been created. The implementer must supply the implementation (e.g., a Python/JS script) and the resulting bar‑chart image or file.
- **T030** — No code, notebook, script, or generated figure for a partial dependence plot of the top predictor (FR‑007) is present. The required artifact (implementation and/or visual output) is missing, so the task is not satisfied.
- **T032** — declared artifact(s) missing/empty/invalid: data/results/interpretation.md
