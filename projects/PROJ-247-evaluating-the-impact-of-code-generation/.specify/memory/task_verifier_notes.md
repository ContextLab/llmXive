# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — declared artifact(s) missing/empty/invalid: data/raw/code_blocks.csv
- **T012b** — The required output files `data/logs/refactor_exclusions.log` and `data/logs/refactor_validation_report.json` are missing, and there is no evidence that the `GitMvDetector` implementation and `run_refactor_verification` logic have been added or produce the specified logs. Without these artifacts (and passing the unit tests), the task is not satisfied.
- **T013** — The provided `code/01_data_curation.py` shows imports and constants for the classifier and log file, but the visible portion does not contain any code that actually runs the CodeBERT classifier, tags blocks, checks the confidence threshold, or writes exclusions to `data/logs/classifier_exclusions.log`. Moreover, the required log file is missing from the repository. The task’s core functionality and logging artifact are therefore not present.
- **T015** — The `matching.py` implementation uses a placeholder random‑number propensity score instead of fitting a logistic regression on `cyclomatic_complexity` and `LOC`, and the file is truncated before completing the match‑pair dataframe. Moreover, the required output `data/processed/matched_pairs.csv` does not exist. Both the algorithmic requirement and the expected output artifact are missing.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/matched_pairs.csv, data/processed/matched_pairs_filtered.csv, data/logs/repo_exclusions.csv
- **T017b** — declared artifact(s) missing/empty/invalid: tests/unit/test_classifier_metrics.py, data/ground_truth/classifier_metrics.json
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/metrics_longitudinal.csv
- **T022** — The required output file `data/processed/metrics_longitudinal.csv` is missing, so no code churn data has been produced or appended as specified. The task’s core artifact does not exist.
- **T023** — The required log file `data/logs/latency_exclusions.log` does not exist, so the edge‑case handling and logging specified in the task have not been delivered. The implementer must create this file and populate it with entries of the form `pair_id, reason` for each excluded pair.
