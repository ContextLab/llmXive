# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The evidence confirms `src/` exists with the four sub-directories, but the collector explicitly reports `models/` as MISSING, and there is no evidence of an `__init__.py` inside `data/`, `models/`, `evaluation/`, or `utils/` — only the top-level `src/__init__.py` is shown. The task's verification criterion (an empty `__init__.py` in each sub-module) is therefore not satisfied; the implementer must create the missing `models/` directory (or resolve the path discrepancy) and add the per-sub-module `__init__.py` markers.
- `T003` (rejected 1x): Requested task execution failed; rerun successfully: code/run_linting.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

