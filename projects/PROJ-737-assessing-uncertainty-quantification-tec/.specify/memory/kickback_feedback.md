# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The `code/download.py` script and its tests succeed, but the downloaded files are not the required materials datasets. The CSVs contain the Iris, Tips, and Planets example data from seaborn, and the metadata `source_url` fields point to those unrelated URLs instead of the OQMD/AFLOW URLs specified in the task. Consequently the core requirement of fetching the three real materials property datasets is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

