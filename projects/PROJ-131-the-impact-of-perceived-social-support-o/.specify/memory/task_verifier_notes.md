# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No `main_pipeline.py` file or any code configuring an entry point to orchestrate the modular steps (data ingestion, weighting, regression, etc.) is present in the provided artifacts. The required orchestrating script is missing, so the task is not satisfied.
- **T018** — No code, log file, or documentation was provided showing that the GSS 2022 structure is validated, that missing PCL‑5 or harassment variables trigger a warning and cause the GSS ingestion to be skipped, and that the fallback to the Cyberbullying dataset alone is documented. The required artifact is missing.
- **T015** — No artifacts (e.g., a synthetic cohort CSV, covariate balance statistics, or regression output files) were provided; the claim cannot be verified against any concrete data or code. The required deliverables are missing, so the task is not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/results/synthetic_cohort.csv
- **T017** — No logging implementation, configuration, or example log output was provided; the claim lacks any artifact showing added comprehensive logging for the ingestion, preprocessing, matching, and validation steps (including fallback decisions). The required code/files are missing, so the task is not satisfied.
- **T019** — The required artifact `tests/unit/test_bootstrap_ci.py` does not exist in the repository, so no unit test for the bootstrapping logic is present. The task cannot be considered completed until this file is added with appropriate test code.
- **T022** — No code, script, or log file was provided that demonstrates the addition of a fallback mechanism to refit a standard OLS model when the robust model fails to converge, nor evidence that the status `E‑NONCONV‑001` is logged. The required artifact is missing.
- **T024** — declared artifact(s) missing/empty/invalid: data/results/regression_results.csv
- **T029** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_analysis.csv
