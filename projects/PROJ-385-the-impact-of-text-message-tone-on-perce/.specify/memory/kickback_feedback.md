# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required output file `data/processed/counterbalanced_trials.csv` is missing, so the counterbalancing task does not actually produce the CSV that should contain rows for every stimulus‑context pair per participant. Without this file, the task’s core requirement is unmet.
- `T051` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/real_ratings.csv, data/processed/anonymised_ratings.csv
- `T086` (rejected 1x): The required file `data/processed/anonymised_ratings.csv` is missing, so there is no data to validate the `participant_id` column against the Participant schema. The task cannot be considered completed until this file exists and contains a non‑null `participant_id` column as specified.
- `T054` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/real_ratings.csv, data/checksums.json
- `T052` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/anonymised_ratings.csv, data/checksums.json
- `T037a` (rejected 1x): The required file `code/run_pipeline.py` does not exist in the repository, so there is no CLI entry point to test for `--mode real` or `--help` output. The task’s core deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

