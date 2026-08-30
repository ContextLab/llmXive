# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): The required output file `data/processed/ablation_labels_train.json` is missing, and the input file `data/raw/agenticsts_trajectories.jsonl` (and the referenced schema) are also absent, so the ablation study could not have been run to generate the ground‑truth labels.
- `T008d` (rejected 1x): The log file exists but does not contain a CRITICAL entry as required, and the required `data/processed/fallback_flag.json` file is missing entirely. Consequently the task’s failure‑handling and fallback artifact are not satisfied.
- `T006a` (rejected 1x): The provided `code/parser.py` does not raise a `FileNotFoundError` when `data/raw/` is missing/empty, nor does it raise a `ValueError` on schema mismatches; it merely logs errors and returns `False`. It also lacks any logic to read the raw logs, extract per‑turn metrics, and write `data/processed/metrics_with_moves.csv`. Additionally, the required schema file `contracts/trajectory.schema.yaml` and the output CSV are absent.
- `T006b` (rejected 1x): The provided `code/entropy.py` is truncated and does not contain logic to read `metrics_with_moves.csv`, compute entropy per row, handle NaN/Infinity warnings, or write `entropy_metrics.csv`. Moreover, the required input, output, and log files are absent, and the `extract_move_distribution` function is incomplete (returns an undefined variable). The task’s skip‑condition and edge‑case handling are not demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

