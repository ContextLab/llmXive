# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided that the required directories (`projects/PROJ-312-evaluating-the-impact-of-code-generation/` with subfolders `code/`, `data/`, `tests/`, `contracts/`, `artifacts/`, `state/`) actually exist; the response contains only the task description and no file‑system listing or screenshots. The implementer must create and show the directory structure.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/pyproject.toml
- `T008` (rejected 1x): No evidence was presented showing that the required directories (`data/raw/`, `data/processed/`, `data/spot_check/`, `artifacts/`, `tests/`) actually exist in the repository; the claim is unsubstantiated. The implementer must provide a directory listing or screenshots confirming the presence of these folders.
- `T012b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/pr_turnaround_partial.csv, data/processed/truncated_repos.txt
- `T014` (rejected 1x): The `code/fetch_data.py` file shown does not contain any logic that checks `MIN_PR_THRESHOLD` or writes skipped repository names to `data/processed/excluded_repos.txt`. Moreover, the required `data/processed/excluded_repos.txt` file is absent. The task’s core requirement—skipping repos with fewer than the configurable threshold and recording them—is therefore not fulfilled.
- `T023a` (rejected 1x): The repository lacks the required input files `data/processed/excluded_repos.txt` and `data/processed/pr_turnaround.csv`; without them the implemented `code/analyze.py` cannot actually load and validate the data as the task demands. The script’s fallback for a missing excluded‑repos file is present, but the essential CSV file is absent, causing a `FileNotFoundError`. These missing artifacts must be added for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

