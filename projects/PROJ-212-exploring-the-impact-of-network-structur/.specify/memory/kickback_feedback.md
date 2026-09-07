# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory `projects/PROJ-212-exploring-the-impact-of-network-structur/code/` or any files within it was provided; without a visible project structure the task requirement is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook) are present in the provided artifacts, nor any documentation showing that Ruff and Black have been set up for the project. Without these concrete files, the task of configuring linting and formatting tools is not satisfied.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_models.py
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/loader.py, data/synthetic_fallback_N30.csv
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils.py
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/validators.py
- `T010` (rejected 1x): The test file `tests/test_topology.py` is present and contains realistic assertions, but the required source module `src/topology.py` does not exist, so the tests cannot be imported or executed. The missing implementation file must be added (or the import path corrected) for the unit test to be functional.
- `T011` (rejected 1x): The required source file `src/simulation.py` is missing, so the imported functions (`check_disconnected`, `kuramoto_derivative`, `run_kuramoto_simulation`) do not exist. Additionally, the provided `tests/test_simulation.py` is truncated and incomplete (e.g., an unfinished fixture definition), meaning the unit tests are not fully defined or runnable. Both the implementation and the complete test suite are absent.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/topology.py
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/simulation.py
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/simulation.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: results/sim_results.json
- `T017b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/simulation.py, results/verification_report.json
- `T018` (rejected 1x): The required `src/stats.py` file does not exist, so there is no code to test, and consequently no unit test for VIF calculation or Ridge fallback logic can be present or validated. The missing source file must be added (with the VIF and Ridge logic) and a corresponding unit test created to satisfy the task.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: src/stats.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

