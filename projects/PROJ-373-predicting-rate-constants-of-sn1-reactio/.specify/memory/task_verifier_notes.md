# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No pytest configuration, test files, or YAML schema contract tests were supplied; the claim lacks any artifact to verify that pytest has been set up to validate YAML schemas. The required files are missing, so the task is not satisfied.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_report.csv
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_sn1.csv
- **T022** — No `artifacts/best_model.pt` or `artifacts/metrics.json` files are presented, and the response contains no code, logs, or data showing that the best model weights and metrics were actually saved. Without these concrete artifacts, the task requirement is not satisfied.
- **T023** — No `artifacts/hyperparameter_search.log` file was presented, and no content showing logged hyperparameter configurations and validation scores is available. Without the required log artifact, the task requirement is not satisfied.
- **T030** — The response contains no `artifacts/feature_importance.png`, `artifacts/sensitivity_report.csv`, or `artifacts/perturbation_results.csv`; no files or their contents are shown, so the required outputs are missing.
- **T031** — No evidence of the `specs/001-predict-sn1-rate-constants/quickstart.md` file or its updated contents was provided; without the actual markdown artifact we cannot confirm that the required documentation changes were made.
- **T033** — No integration-test artifacts (e.g., logs, output CSVs, model files, or a report showing the pipeline run on a small subset) were supplied. Without concrete evidence that the full end‑to‑end pipeline was executed and verified, the task requirement is not satisfied. The next implementer must provide the execution logs, resulting processed data, trained model checkpoint, and a summary confirming successful completion of each pipeline stage on the test subset.
- **T034** — No artifact (e.g., a report, script output, or updated `quickstart.md` showing that the steps run successfully) was provided; the implementer gave no evidence that the quickstart guide was executed and validated. The required validation is therefore missing.
