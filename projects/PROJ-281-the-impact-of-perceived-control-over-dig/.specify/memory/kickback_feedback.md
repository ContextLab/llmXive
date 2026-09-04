# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No evidence of the `data/raw/` and `data/processed/` directories or their required `.gitkeep` placeholder files is present; without these artifacts the task requirement is not satisfied.
- `T009` (rejected 1x): No pytest configuration files (e.g., pytest.ini, setup.cfg, or pyproject.toml) or test suite files that enable `pytest-cov` are present in the provided evidence, so the requirement to configure pytest with coverage in the `tests/` directory is not satisfied. The implementer must add the appropriate configuration and ensure it is non‑empty.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

