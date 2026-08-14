# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015a` (rejected 1x): The provided `code/analysis/narrative_logic.py` is truncated and does not contain a complete implementation (it ends abruptly with “ret”). Moreover, the required input files `data/processed/extracted_studies.csv` and `data/config/narrative_methodology.yaml` are absent, and the expected output `data/derived/narrative_themes.json` was never created. The task’s core functionality cannot be verified or executed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

