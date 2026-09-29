# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No `project_structure.txt` file or directory listing was supplied, and there is no evidence that the requested directories (`code/utils`, `data/raw`, etc.) actually exist. The implementer must provide the `ls -R` output (or equivalent) and the generated `project_structure.txt` containing the full directory tree.
- `T024` (rejected 1x): The provided `code/data_ingestion.py` lacks the required assertion that the downloaded count meets the `RSS_SIZE` configuration and does not include logic to obtain a large list of material IDs (the source CSV is missing). Moreover, the expected output file `data/raw/raw_pool.csv` does not exist. These missing pieces mean the task’s requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

