# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T060a` (rejected 1x): `code/lint_report.txt` exists but records "Exit code: 1" with ~40 unresolved flake8 findings (E302, F841, W503, E501, F821, etc.) across `code/` and `tests/`. The deliverable explicitly requires exit code 0 and a clean re-run of `flake8 code/ tests/`; the report itself documents that the lint issues were not fixed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

