# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No code, configuration files, or documentation were presented that demonstrate loading settings from a `.env` file or providing default values. The required artifact for environment configuration management is missing, so the task is not satisfied.
- `T022` (rejected 1x): The repository contains `code/data/preprocess.py`, but the shown code stops before any saving step and the required output file `data/processed/cleaned_data.fif` is absent. Consequently the script does not actually create the cleaned‑data artifact nor produce the trial‑rejection log as mandated. The missing artifact must be generated and the script must include the saving and logging logic.
- `T032` (rejected 1x): The repository lacks the required `data/results/metrics_summary.json` file, and the shown portion of `code/main.py` does not demonstrate a call to the extraction step followed by writing that JSON file. Without the file and clear code that performs the save, the task is not fulfilled.
- `T036` (rejected 1x): The claim provides only the task description; there is no GitHub Actions workflow, run logs, or any evidence that the full pipeline was executed on the free‑tier runner and stayed within the 7 GB RAM / ≤6 h limits. Without these artifacts the CI integration test cannot be verified.
- `T039` (rejected 1x): The provided `code/analysis/source.py` contains only head‑model and forward‑solution setup code; there is no implementation of a spatial‑smoothing kernel sweep, Coefficient of Variation calculation, or CSV export. Moreover, the required output file `data/results/sensitivity_analysis.csv` does not exist. Both the functional code and the expected result artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

