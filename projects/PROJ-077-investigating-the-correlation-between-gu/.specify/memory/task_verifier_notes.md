# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020b** — No code, test, or documentation was provided showing a verification step that checks column types and raises the required `ValueError`. The required artifact implementing this logic is missing.
- **T022** — The repository lacks `data/processed/correlation_results.csv`, and the provided `code/analysis.py` snippet does not contain any implementation of the required Spearman rank correlation (no function checking raw counts, raising `ValueError`, or writing the `r_value`, `p_value`, `n_obs` columns). The task’s core functionality and output file are missing.
- **T024** — The repository contains a `calculate_vif` implementation and a `save_vif_results` function that would write `data/processed/vif_results.json`, but the JSON file is not present on disk, and the provided code snippet does not show the function being invoked to generate it. Hence the required output artifact is missing.
- **T025c** — declared artifact(s) missing/empty/invalid: data/processed/analysis_warnings.log
- **T025b** — The repository lacks the required `data/processed/regression_diagnostics.json` file, and the provided `code/analysis.py` excerpt does not contain any implementation of a Shapiro‑Wilk test on OLS residuals or logic to write a validation report. Consequently, the task’s core requirement is not satisfied.
- **T029b** — declared artifact(s) missing/empty/invalid: data/processed/lasso_results.csv
- **T029c** — The `code/analysis.py` file shown does not contain any implementation of a Shapiro‑Wilk test on Lasso residuals nor code that writes a JSON report to `data/processed/lasso_diagnostics.json`. Moreover, the required `lasso_diagnostics.json` file is absent from the repository. The task’s core requirement is therefore not satisfied.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
