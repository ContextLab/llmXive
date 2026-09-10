# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure was presented or listed; the claim provides no evidence that the required folders (`code/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `tests/`, `state/`) actually exist on disk. The implementer must create and show the project hierarchy to satisfy the task.
- `T007` (rejected 1x): No `state/projects/PROJ-386...yaml` file (or any equivalent YAML schema) was presented, and there is no evidence that a schema for artifact hashing and checksums was created. The required artifact is missing, so the task is not satisfied.
- `T023` (rejected 1x): The provided `preprocessing.py` contains data loading, interaction generation, and normalization code but shows no function that computes pairwise correlations, flags pairs with correlation > 0.8, or writes a JSON report. Moreover, the required `data/artifacts/collinearity_report.json` file does not exist. Both the core functionality and the output artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

