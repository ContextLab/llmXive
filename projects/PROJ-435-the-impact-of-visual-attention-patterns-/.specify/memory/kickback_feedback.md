# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The required input `data/derived/empirical_outcomes.csv` and the expected output `data/derived/valence_scores.csv` are absent, so the script cannot be exercised or verified. Moreover, the provided `code/03_valence_calculation.py` is truncated and does not show the implementation of the NRC‑coverage calculation, the 50 % fallback to VADER, or the logging of a lexicon switch to `state/runtime_events.json`. These core pieces are missing, preventing the task from being considered fulfilled.
- `T007` (rejected 1x): The repository contains a `code/02_data_quality_report.py` file, but it is truncated and does not include the logic to read the exclusion log, compute counts/reasons, or write `output/data_quality_report.csv`. Moreover, the required input `data/derived/preprocessed_gaze.csv` is absent, and no generated `output/data_quality_report.csv` is present. The task’s core output and necessary inputs are therefore missing.
- `T024` (rejected 1x): The required input file `data/derived/merged_dataset_full.csv` is absent, so the script cannot run. Moreover, the provided `code/05_regression_analysis.py` is truncated and never reaches the part where a mixed‑effects model with random intercepts for Participant and Headline is fitted, so the core task requirement is not met.
- `T023` (rejected 1x): The provided `code/04_data_merge.py` is truncated (e.g., the `load_valence_scores` function is incomplete) and does not contain the full merging logic. Moreover, the required input files `data/derived/preprocessed_gaze.csv` and `data/derived/valence_scores.csv` are missing, so the script cannot be executed or validated. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

