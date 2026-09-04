# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was presented showing that the directories `code`, `tests`, `data`, and `artifacts` exist under `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/`; the claim is unsubstantiated. The required folder structure must be created and verified.
- `T002` (rejected 1x): The submission provides no visible evidence that the directories `data/raw`, `data/processed`, and `data/split` actually exist in the repository; no file listings, screenshots, or code creating them are present. Consequently the required data subdirectories are missing.
- `T003` (rejected 1x): No evidence was presented showing that the required subdirectories (`artifacts/models`, `artifacts/reports`, `artifacts/figures`) actually exist or contain any files; the claim is unsupported. The next implementer must create these directories (and optionally add placeholder files) and provide a listing or screenshot confirming their presence.
- `T007` (rejected 1x): The `code/generate_synthetic.py` script is truncated and never reaches the step that writes the DataFrame to `data/raw/synthetic_baseline.csv`. Moreover, the expected CSV file does not exist in the repository. The deterministic generator and required output file are therefore missing.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: conftest.py
- `T009` (rejected 1x): No `.env` file, constants module, or any configuration artifact is present in the provided evidence, and thus there is no evidence that `N_PERMUTATIONS=1000` has been defined for statistical tests. The required environment configuration file is missing.
- `T012` (rejected 1x): The required source file `data/raw/synthetic_baseline.csv` does not exist, and the expected output files `data/processed/validated.csv` and `artifacts/reports/validation_log.json` are missing. Moreover, `code/ingest.py` contains only helper functions and no orchestration that loads the specified CSV and writes the required outputs.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

