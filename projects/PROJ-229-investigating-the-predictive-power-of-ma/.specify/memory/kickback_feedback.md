# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `data/results`, `data/external`) is provided; the implementer did not supply any file‑system listing, script output, or screenshots confirming their creation. The task remains undone until those directories exist and are shown.
- `T001b` (rejected 1x): No evidence of the required directories (`code/data`, `code/models`, `code/utils`) is provided; the artifact list is empty, so the claim that the code directories were created cannot be verified.
- `T001c` (rejected 1x): The claim provides no concrete evidence (e.g., a directory listing, screenshots, or file tree) that the required `tests/unit`, `tests/integration`, and `tests/contract` directories actually exist in the repository. Without such proof, we cannot verify that the task was completed.
- `T006b` (rejected 1x): The required file `contracts/target_decision.schema.yaml` does not exist (listed as missing), so no JSON schema has been provided. The task’s core artifact is absent.
- `T005a` (rejected 1x): The provided `fetch_materials.py` is truncated; the visible portion stops before the query execution and never shows the fallback to the `matbench` dataset, the validation of a `material_id` column, the JSON‑write step, or the required `FileNotFoundError`. Moreover, the expected output file `data/raw/materials_project_data.json` is absent, indicating the script either does not create it or has not been run. The implementation must be completed to include the fallback logic, ID verification, error handling, and saving of the fetched data.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

