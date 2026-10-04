# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): No evidence of a `results/logs/` directory, logging configuration files, or code that writes data quality logs and model diagnostics to that path was provided. The required logging infrastructure artifact is missing.
- `T014` (rejected 1x): No pytest configuration files (e.g., pytest.ini, conftest.py) or related code were presented, so there is no evidence that a CPU‑only execution mode or stratified‑sampling fixtures/markers have been set up. The required artifact is missing.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/era5_sample.h5, state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
- `T006` (rejected 1x): The implementer’s artifact list shows that `data/raw/moral_machine.csv.gz` does not exist, so the validation gate cannot confirm the required file’s presence. Consequently the task’s requirement to verify both `data/raw/era5_raw_chunks/` and `data/raw/moral_machine.csv.gz` is not satisfied. The missing CSV file must be added (or correctly generated) for the task to be complete.
- `T022a` (rejected 1x): declared artifact(s) missing/empty/invalid: results/logs/match_success_rate.json
- `T028b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/dilemma_choices.csv
- `T028d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/time_of_day.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

