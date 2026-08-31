# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The provided material only describes user stories for cognitive‑load modeling and contains no linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, `black` settings) or evidence that ruff, flake8, and black have been set up. Consequently the task “Configure linting (ruff/flake8) and formatting (black) tools” is not satisfied. The missing artifacts need to be added and verified.
- `T023` (rejected 1x): The required output file `data/explanation_tiers/simple_tiers.csv` does not exist, so the implementation and iterative refinement loop cannot be verified. The missing CSV means the task’s core deliverable is absent.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/explanation_tiers/complex_tiers.csv
- `T025` (rejected 1x): No CSV or JSON files were presented in `data/explanation_tiers/`, nor any code showing that generated tiers and their metadata are being written to that directory. The required output files are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

