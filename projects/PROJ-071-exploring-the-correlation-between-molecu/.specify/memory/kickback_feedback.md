# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository contains a `log_error_to_file` helper and a `validate_molecule` that raises a custom `AtomValenceException`, but there is no code that catches this exception and calls the logger, and the required `data/processed/excluded_molecules.csv` file does not exist. The task’s core requirement—automatically logging non‑standard‑valence molecules to the CSV—has not been fulfilled.
- `T055` (rejected 1x): The required output artifacts are absent: `data/processed/merged_drugs.csv`, `data/processed/analysis_results.json`, the report file (`results_report.md` or `data_insufficiency_report.md`), and `reproducibility_log.json` are not present on disk, so the pipeline smoke test has not been verified as successful.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

