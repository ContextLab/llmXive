# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`src/models`, `src/data`, `src/training`, `src/experiments`, `src/utils`, `tests/unit`, `tests/integration`, `scripts`, `data/results`, `data/logs`, `data/configs`, `state`) is provided; the implementer’s claim cannot be verified without actual filesystem artifacts.
- `T001b` (rejected 1x): No `__init__.py` files were found in the `src/` and `tests/` directories, and a `.gitignore` file is absent (or its contents were not provided). Consequently the required files and the specific ignore rules (excluding `data/`, `__pycache__`, `*.pyc` while ensuring `state/*.yaml` is **not** ignored) are missing. The implementer must add the `__init__.py` files and create a correctly configured `.gitignore`.
- `T019a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/training/homeostasis.py
- `T026b` (rejected 1x): The provided `src/experiments/ablation.py` is truncated and does not contain a `run_ablation_study` function that loops through configs, trains models, computes MAE, and writes results. Moreover, the required output file `data/results/ablation_results.json` is absent. These missing pieces prevent the task from being fulfilled.
- `T027` (rejected 1x): declared artifact(s) missing/empty/invalid: src/experiments/scaling.py, data/results/scaling_results.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

