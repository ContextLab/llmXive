# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000a` (rejected 1x): No `methodology_rationale.md` file was supplied; there is no evidence of a document describing the conflict between Constitution Principle VI (Pearson/McNemar) and the required Point‑Biserial/Spearman/Paired Permutation methods, nor any scientific justification for the deviation. The required artifact is missing.
- `T001a` (rejected 1x): No evidence of the required directories (`code/`, `code/src/`, `code/tests/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`, `specs/001-code-complexity-bug-prediction/`) being created is provided; the claim lacks any artifact listing or screenshots confirming their existence. The implementer must supply a view of the filesystem (e.g., a tree listing) showing these folders.
- `T001c` (rejected 1x): No evidence of a Python 3.11 virtual environment (e.g., a `venv` directory, activation script, or `pyproject.toml`/`requirements.txt` showing it was created) is present. The implementer provided only a high‑level feature specification unrelated to the task, so the required artifact is missing.
- `T006` (rejected 1x): The required file `code/src/labeling.py` does not exist in the repository, so no function signatures or interface definitions are present. The task’s core deliverable is missing.
- `T014b` (rejected 1x): No Python wrapper script integrating the PMD CLI is present in the provided evidence; there is no file, code snippet, or description of such a script, nor any output showing cyclomatic complexity values per Java file. The required artifact is missing, so the task is not satisfied.
- `T014c` (rejected 1x): No Python wrapper script or any related code was presented; the evidence lacks the required artifact entirely, so the task of implementing a wrapper to invoke the JavaParser‑based Halstead Volume calculator for every Java file is not satisfied.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: code/src/labeling.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

