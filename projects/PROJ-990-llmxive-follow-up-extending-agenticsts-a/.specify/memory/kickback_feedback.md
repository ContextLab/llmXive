# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): The repository lacks the required `data/processed/metrics_with_moves.csv` file, and the provided `code/parser.py` is incomplete (the `extract_move_distribution` function is truncated and there is no code that writes the extracted metrics and move distributions to a CSV). The task’s core output is therefore missing.
- `T005` (rejected 1x): The provided `code/entropy.py` does not contain the required logic to write the exact warning “Warning: NaN/Inf entropy detected at trajectory {id}, turn {turn}” to `data/processed/edge_case_warnings.log`, nor does it show any code that reads `data/processed/metrics_with_moves.csv` and processes trajectories. Additionally, both `data/processed/edge_case_warnings.log` and `data/processed/metrics_with_moves.csv` are missing from the repository. The implementation therefore does not meet the task specifications.
- `T014a` (rejected 1x): The required output files (`train_set.csv`, `ablation_train_set.csv`, `validation_set.csv`, `test_set.csv`, and `validation_set_ids.json`) are absent, and the provided `code/splitter.py` is incomplete (truncated) and contains no logic to write those files. The task’s core deliverables are therefore not satisfied.
- `T007b` (rejected 1x): The required `data/processed/validation_set.csv` file is absent, and the expected output `data/processed/static_log_proxy.json` was not generated. Moreover, the provided `code/parser.py` (truncated) shows no implementation of the static‑log‑derived utility extraction described in the task. The necessary input and output artifacts, as well as the corresponding code changes, are missing.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/ablation_train_set.csv, data/processed/ablation_labels_train.json
- `T008b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/validation_set.csv, data/processed/ablation_labels_validation.json
- `T017` (rejected 1x): The required output file `data/processed/simulation_logs_dynamic.json` is missing, so the dynamic simulation was not executed and no results were produced. The task’s primary deliverable is absent.
- `T020` (rejected 1x): The repository contains `code/engine_runner.py` with a stub implementation for the “random” policy, but the required output file `data/processed/simulation_logs_random.json` is absent, and there is no evidence that the runner was invoked on the test set to produce it. The task’s primary deliverable is therefore missing.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/baseline_comparison.csv
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/token_consistency_report.json, data/processed/baseline_comparison.csv
- `T022a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/token_reduction_verification.json, data/processed/baseline_comparison.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

