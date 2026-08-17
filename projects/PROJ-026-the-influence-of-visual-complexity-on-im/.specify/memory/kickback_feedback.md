# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The required output file `data/processed/complexity_scores.csv` does not exist, and the provided `code/stimuli/process.py` is truncated before any code that writes the CSV, so we cannot verify that it produces the required schema. The task’s core deliverable is therefore missing.
- `T018` (rejected 1x): No code, notebook, script, or output file was provided that actually computes visual‑complexity scores and applies `pandas.qcut` to assign Low/Medium/High categories. Without the required artifact (e.g., a Python module or CSV showing the categorized images), the task’s requirement is not satisfied.
- `T026` (rejected 1x): The `load.py` script lacks any command‑line handling for a `--null-effect` flag and does not raise a `RuntimeError` when synthetic data is loaded in production mode. The `process.py` file never aggregates per‑participant scores, writes the required `aggregated_d_scores.csv`, or produces the specified columns (`participant_id, session_id, d_score, n_trials_valid, status`). The expected output file is missing entirely.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

