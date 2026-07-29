# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009c` (rejected 1x): The provided `code/data_extraction.py` does not use `openml.datasets.get_dataset()` as required, never writes the extracted data to `data/raw/openml_aluminum.json`, and the file is truncated (missing the rest of the implementation). Moreover, the expected output file `data/raw/openml_aluminum.json` is absent. These gaps mean the task’s core requirements are not met.
- `T016` (rejected 1x): The claimed implementation does not create the required `data/raw/openml_aluminum.json` file (it is missing), and `code/main.py` contains no code that runs the T009c extraction function or writes that intermediate raw file. The task’s core output is therefore not present.
- `T017` (rejected 1x): The required output file `data/processed/filtered_alloys.csv` does not exist, and the provided `code/main.py` excerpt shows only imports and helper functions without actually invoking the cleaning pipeline or writing that CSV. Hence the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

