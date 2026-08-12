# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): No evidence was provided showing that a `data/` directory and a `results/` directory actually exist in the repository, nor that each contains a `.gitkeep` file. The implementer’s claim cannot be verified without these artifacts. The next implementer should add the two directories and place an empty `.gitkeep` file inside each.
- `T008` (rejected 1x): No logging configuration file, code snippet, or any other artifact that sets up logging to `logs/pipeline.log` and records exclusion reasons was provided; the claim lacks concrete evidence of the required infrastructure.
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: results/metrics.json
- `T031` (rejected 1x): declared artifact(s) missing/empty/invalid: results/model.pkl, results/metrics.json
- `T037` (rejected 1x): declared artifact(s) missing/empty/invalid: results/model.pkl
- `T040` (rejected 1x): declared artifact(s) missing/empty/invalid: results/screening_full.csv
- `T041` (rejected 1x): declared artifact(s) missing/empty/invalid: results/screening_candidates.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

