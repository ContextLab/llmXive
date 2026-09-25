# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012c` (rejected 1x): The required output file `data/raw/khan_academy.csv` (and its checksum) is missing, so the deliverable is not present. Additionally, the provided script is truncated and does not show the logic that exits with code 1 and logs the exact required error message on timeout. The task therefore remains unfinished.
- `T012a` (rejected 1x): The `validate_unified_schema.py` file is present but ends abruptly (truncated code) and lacks a complete implementation (e.g., main entry point, full row validation, exit handling). Moreover, the required data files `data/raw/unified_problems.csv` and `contracts/problem.schema.yaml` are missing, so the script cannot be executed to verify the schema as specified. The task’s deliverable is therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

