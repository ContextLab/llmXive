# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T1201a` (rejected 1x): The implementer did not provide any artifact (e.g., a text file, JSON, or console output) listing the `t0*.py` files found in the `code/` directory. Without such a list, the requirement to audit and generate the file list is not satisfied. The next implementer must produce a non‑empty list of matching filenames from the `code/` directory.
- `T1201b` (rejected 1x): No migration plan document (e.g., a markdown, text, or spreadsheet listing the `t0*.py` files and the steps to migrate them) was provided, and there is no evidence that such a plan covers all identified files. The required artifact is missing, so the task is not satisfied.
- `T1204` (rejected 1x): No evidence was provided that any `t0*.py` files were removed from the `code/` directory, nor is there a verification artifact (e.g., a file listing or test output) confirming that `code/` contains no such files. The implementer must supply proof that the deletion was performed and that T1204a passes.
- `T1205` (rejected 1x): No audit report or any list of hard‑coded path strings from the Python modules in `code/` was provided; the required artifact T1205a is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

