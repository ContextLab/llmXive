# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository contains a `code/filter.py` file, but it is truncated (e.g., `write_filter_log` ends abruptly) and lacks a script entry point that actually runs the filter and writes `data/processed/organophosphates_filtered.csv`. Moreover, the required output CSV file is absent from the `data/processed` directory. Consequently, the task’s core requirement—filtering compounds with the specified SMARTS pattern and saving the results to the designated CSV—is not fulfilled.
- `T013b` (rejected 1x): The repository lacks `data/processed/sample_size_status.json`, and the provided `code/filter.py` excerpt shows no function that writes such a JSON file based on sample size. Consequently, the required output and logic are absent.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/filter_log.txt
- `T024` (rejected 1x): The required `data/processed/final_test_metrics.json` file is absent, and the provided `code/evaluate.py` neither contains logic to read that JSON nor is the script complete (it is truncated and lacks the necessary functionality). The task’s core requirement is therefore unmet.
- `T025a` (rejected 1x): The provided `code/evaluate.py` is incomplete (truncated) and does not contain an implementation of the Corrected Resampled t‑test (Nadeau & Bengio) on K‑Fold ROC‑AUC scores. Moreover, the required input file `data/processed/kfold_scores.json` is missing entirely. Both the necessary artifact and the required functionality are absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

