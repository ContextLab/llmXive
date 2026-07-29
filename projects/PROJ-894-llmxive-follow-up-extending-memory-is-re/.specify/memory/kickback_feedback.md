# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T033` (rejected 1x): The repository contains `code/utils/validate_results.py`, but the required schema file `contracts/results.schema.yaml` is missing, so the script cannot validate against the official contract and falls back to a hard‑coded default. Moreover, the provided script is truncated and does not show the full validation logic for all six CSV files. The task’s requirement of a schema‑validation script that uses the contract file is therefore not satisfied.
- `T013b` (rejected 1x): The required input graph file `data/processed/graphs/graph_noise_42.json` does not exist, and the expected results CSV `data/processed/noisy_baseline_results.csv` is also missing. Moreover, `code/runner.py` contains only generic task‑running utilities and does not implement the noisy‑baseline execution or logging of `task_id`, `accuracy`, `nodes_visited`, and `latency_ms`. The task therefore has not been fulfilled.
- `T019` (rejected 1x): The repository contains a generic `code/runner.py` but it does not include any logic specific to executing Lazy or Greedy strategies, nor does it write results to the required `data/processed/lazy_results.csv` and `data/processed/greedy_results.csv`. Both CSV files are missing, so the required artifacts are absent. The task’s core requirement—runners that log the outcomes of the Lazy and Greedy executions to the specified files—has not been fulfilled.
- `T019b` (rejected 1x): The repository lacks the synthetic noisy graph file (`graph_noise_42.json`) and the expected result CSVs (`noisy_lazy_results.csv`, `noisy_greedy_results.csv`). Moreover, `code/runner.py` contains only generic task‑running utilities and does not implement the required noisy execution runners for the Lazy and Greedy strategies. These missing artifacts and functionality mean the task’s requirements are not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

