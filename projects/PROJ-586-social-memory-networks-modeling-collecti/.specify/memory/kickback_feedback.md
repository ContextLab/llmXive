# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011c` (rejected 1x): The repository contains a partially‑implemented `run_experiment.py` (imports and a checksum helper) but the code that creates the `data/` directory, computes the checksum of a downloaded file, and writes a `data/manifest.json` matching the required schema is not present (the function is truncated and the manifest file is missing). The task’s core artifact – a populated `manifest.json` – does not exist.
- `T015` (rejected 1x): No `results_full.csv` file was presented in the evidence, nor any proof that it exists at `projects/PROJ-social-memory-networks-modeling-collecti/results/` with the required columns. Without the actual CSV (or a listing showing its presence and contents), the task’s core output cannot be confirmed. The implementer must provide the generated file (or a verifiable directory listing) containing `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, and `agent_count` for the appropriate number of games.
- `T022` (rejected 1x): The repository contains `code/analysis/sensitivity.py`, but the file is only partially shown and there is no `results/sensitivity_trend.csv` produced (the file is missing). Without the output CSV, the required aggregation and calculation cannot be confirmed as completed. The next implementer must ensure the script writes the CSV with the specified columns and creates the file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

