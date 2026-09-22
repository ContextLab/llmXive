# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The `data_ingestion.py` file is present but appears truncated and lacks concrete download and manifest‑generation logic, and the required output file `data/results/manifest.csv` does not exist. Both the functional implementation and the expected CSV artifact are missing.
- **T013** — No code, script, or log files were provided showing the added logic to detect missing acute/chronic time points, skip those subjects, and record the exclusion reasons. Without concrete artifacts (e.g., updated ingestion/analysis script, unit tests, or example logs), the claim cannot be verified.
- **T014** — The submission contains no code, tests, or documentation showing that logic was added to detect an AAL atlas failure, skip the affected subject, and log an error without crashing. No artifact addressing this edge‑case is present in the provided materials.
- **T016** — The required output file `data/results/bootstrapped_ci.json` is absent, and the provided `code/bootstrapping.py` snippet does not show the actual contingency logic (checking `n < 20` and invoking bootstrapping). Both the generated result and clear implementation of the switch are missing.
- **T020** — No artifact (e.g., script, function, or notebook) implementing proportional sparsity thresholding on connectivity matrices was provided, nor any documentation or test output showing the thresholding being applied before metric calculation. The claim lacks any concrete evidence of the required functionality.
- **T022a** — declared artifact(s) missing/empty/invalid: data/results/pca_metrics.json
- **T022b** — declared artifact(s) missing/empty/invalid: data/results/descriptive_vif_report.json
- **T023** — No code, script, log file, or test output was provided that demonstrates the system detecting a non‑convergent model fit, logging a warning, skipping the offending subject, and continuing with the rest of the batch. Without such artifact the requirement cannot be verified.
- **T029** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_analysis.csv
- **T031** — declared artifact(s) missing/empty/invalid: data/results/analysis_report.json
