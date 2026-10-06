# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The test file `tests/contract/test_dataset_schema.py` is present, but the required schema file `dataset.schema.yaml` does not exist at the expected path, causing the test fixture to fail and the contract test to be unusable. The missing schema artifact must be added for the task to be satisfied.
- **T012c** — declared artifact(s) missing/empty/invalid: data/processed/behavioral_scores.csv
- **T014** — The provided `code/02_preprocess_eeg.py` does not show any implementation of the median SNR calculation, noise‑band power extraction, NaN/Inf handling, or JSON output generation. Moreover, the required output file `data/processed/snr_metrics.json` is absent. The task’s core functionality and expected artifact are therefore not present.
- **T016** — The repository lacks the required `data/processed/snr_metrics.json` and the generated `data/processed/exclusion_log.csv`. Moreover, the provided `code/02_preprocess_eeg.py` (truncated) does not contain any implementation of the specified data‑quality checks (duration < 60 s, > 20 % corrupted segments, or SNR < 5 dB) nor does it reference the SNR calculation from T014. These essential artifacts and logic are missing.
- **T023** — The required input file `data/processed/correlation_results_fdr.csv` does not exist, and the expected output `data/processed/effect_sizes.json` is also missing. Consequently the script cannot compute or store the partial‑r effect sizes as specified.
- **T025** — No `logs/methodology_notes.md` file was provided, nor any excerpt showing the required explicit “Associational” disclaimer and covariate control summary. Without the actual markdown output, we cannot verify that the task’s deliverable exists or meets the specification. The next implementer must create the `logs/methodology_notes.md` file containing the disclaimer and summary as described.
- **T027** — The repository lacks the required input files (`data/processed/entropy_metrics.csv`, `data/processed/behavioral_scores.csv`) and the expected output file (`data/processed/sensitivity_exclusion_results.csv`). Moreover, the provided `code/04_regression_analysis.py` is truncated and does not contain a complete implementation of the sensitivity analysis or the full regression pipeline. The task therefore remains unfinished.
- **T029** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_exclusion_results.csv, data/processed/sensitivity_threshold_results.csv, data/processed/sensitivity_report.json
- **T031** — declared artifact(s) missing/empty/invalid: reports/final_report.md
- **T032a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T032b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T033a** — declared artifact(s) missing/empty/invalid: docs/diagrams/data_flow.png
