# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — declared artifact(s) missing/empty/invalid: ruff.toml, pre-commit-config.yaml
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The repository contains a partially‑written `tests/contract/test_coverage_schema.py`, but the file is truncated (e.g., the last test method is incomplete) and it expects a real `results/coverage.csv` file rather than a mock JSON as the task specifies. No mock JSON file is provided, and there is no evidence that the test was executed against such a mock. The required artifact (a complete contract test that validates the schema using a mock JSON) is therefore missing.
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/sampling_report.json, data/processed/sample_indices_1000.csv
- **T013c** — The required deliverable `data/processed/sample_indices_10.csv` does not exist on disk, so the sub‑sample selection task has not been provided. The missing file must be created and populated with the appropriate indices to satisfy the requirement.
- **T014** — The required input file `data/processed/sample_indices_1000.csv` is missing, so the script cannot select the 1000‑series subset. Additionally, the provided `run_pipeline.py` is truncated and does not show the full loop with short‑series skipping and model‑convergence error handling, nor any evidence that `state/errors.log` is created after a test run. Both the input artifact and the complete orchestration logic are absent.
- **T015** — The required input `data/processed/sample_indices_1000.csv` is missing, and there is no artifact (e.g., CSV/JSON) showing prediction intervals generated for all series and horizons. Without the input data and the interval output, the task’s core requirement is not satisfied.
- **T016** — The repository contains `code/metrics.py` with an `empirical_coverage` function, but the required output file `results/coverage_intermediate.csv` is missing, and there is no code that generates this CSV for each series/model/horizon. Consequently, the task’s core deliverable (the coverage CSV) is not present.
- **T017** — declared artifact(s) missing/empty/invalid: results/pvalues.json
- **T018** — The required `results/sensitivity_analysis.csv` file does not exist, so no output data was produced. Additionally, the configuration uses `sensitivity_thresholds` instead of the specified `sensitivity_range`, indicating the loop’s parameters are not set as required. Both the artifact and the config key need to be provided correctly.
- **T020** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
