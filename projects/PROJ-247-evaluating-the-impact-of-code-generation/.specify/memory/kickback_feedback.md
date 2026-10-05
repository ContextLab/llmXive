# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/code_blocks.csv
- `T012b` (rejected 1x): The required log file `data/logs/refactor_exclusions.log` and validation report `data/logs/refactor_validation_report.json` are missing, and the provided test suite is incomplete (truncated) with no evidence that the verification logic runs or passes. The implementation and its outputs need to be added.
- `T013` (rejected 1x): The provided `code/01_data_curation.py` only contains setup, block extraction utilities, and imports for the classifier, but the portion that actually runs the CodeBERT ONNX model, tags blocks with “LLM”/“Human” based on a ≥ 0.8 confidence, and writes low‑confidence exclusions to `data/logs/classifier_exclusions.log` is absent (the file is truncated). Moreover, the required `data/logs/classifier_exclusions.log` file does not exist. Consequently, the task’s integration and logging requirements are not satisfied.
- `T015` (rejected 1x): The repository contains a non‑empty `code/utils/matching.py`, but the file is truncated in the evidence and we cannot confirm it implements the full 1:1 nearest‑neighbor matching and writes the required `data/processed/matched_pairs.csv`. Moreover, the expected output CSV is missing entirely. The task’s primary deliverable (the matched pairs file) is not present.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/matched_pairs.csv, data/processed/matched_pairs_filtered.csv, data/logs/repo_exclusions.csv
- `T017b` (rejected 1x): The repository contains the unit test `tests/unit/test_classifier_metrics.py`, but the required output file `data/ground_truth/classifier_metrics.json` is absent, so the calculated precision/recall results were never saved as mandated by the task. The missing JSON file must be generated and stored at the specified path.
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/metrics_longitudinal.csv
- `T022` (rejected 1x): The required output file `data/processed/metrics_longitudinal.csv` is missing, so no code churn data has been produced or appended as specified. The task’s core artifact does not exist.
- `T023` (rejected 1x): The required log file `data/logs/latency_exclusions.log` does not exist, so the edge‑case handling and logging specified in the task have not been delivered. The implementer must create this file and populate it with entries of the form `pair_id, reason` for each excluded pair.
- `T024` (rejected 1x): Both required artifacts are absent: the log file `data/logs/repo_deletion.log` does not exist, and the updated CSV `data/processed/metrics_longitudinal.csv` is missing, so the task’s output and logging requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

