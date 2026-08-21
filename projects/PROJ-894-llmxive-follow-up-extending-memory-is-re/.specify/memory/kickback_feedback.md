# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011a` (rejected 1x): The `data/raw/locomo.jsonl` file does not exist, so the required output was never produced. Additionally, the script’s schema‑mismatch error includes extra text instead of the exact `ValueError("Dataset schema mismatch")` message. The task’s core requirement—downloading the dataset and saving it with the correct columns—is therefore not satisfied.
- `T011c` (rejected 1x): The repository lacks the required output file `data/processed/graphs/graph_noise_42.json`, and `code/data_loader.py` does not contain any logic that calls `inject_noise` to create and save a noisy graph dataset. Consequently the specified pytest check cannot be satisfied. The script must be extended to generate the noisy graph and write the non‑empty JSON file at the expected path.
- `T013b` (rejected 1x): The repository contains a generic `code/runner.py`, but it does not implement a “noisy baseline” execution, does not log the required fields to `data/processed/noisy_baseline_results.csv`, and does not map T006/T037 states to a CSV status column. Moreover, the expected CSV file `data/processed/noisy_baseline_results.csv` is absent. The task therefore remains unfinished.
- `T019a` (rejected 1x): The repository contains a `code/runner.py` file, but it does not include logic that writes the required fields (`task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold`, `status`) to `data/processed/lazy_results.csv`, and the CSV file itself is absent. Consequently the Lazy execution runner and its output file are not actually implemented.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

