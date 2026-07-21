# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No `setup.sh` script or `project_structure.log` file was presented. Without these files, the required directory‑creation script and its verification log are missing, so the task is not satisfied.
- `T002` (rejected 1x): The required file `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/requirements.txt` does not exist, even though a `code/requirements.txt` with version pins is present elsewhere. The task’s deliverable is missing at the specified path.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml, black.toml
- `T004` (rejected 1x): The required `src/utils/entropy_calc.py` file with a `calculate_entropy(logits)` function is missing, and the provided `code/src/utils/entropy_calc.py` defines different functions (`compute_shannon_entropy`, etc.). Additionally, the unit test `tests/unit/test_entropy_calc.py::test_clamp_prevents_log_zero` does not exist. The implementation and test need to be added at the specified locations with the correct API.
- `T005` (rejected 1x): The required artifact `src/utils/validators.py` does not exist at the specified path, and the provided `code/src/utils/validators.py` is truncated (ends mid‑line) and lacks the `EntropyProfile` schema and its validation functions. The deliverable is therefore missing/incomplete.
- `T006` (rejected 1x): The provided `code/src/data/preprocessing.py` is truncated and does not show any `try/except MemoryError` logic nor a retry with reduced batch size, and it lacks the auxiliary functions (`load_tokens_from_file`, `merge_entropy_profiles`, `validate_entropy_profile`) that the integration test imports. Moreover, the required `src/data/preprocessing.py` file is reported missing, and the test suite does not visibly contain the `test_memory_backoff` case that verifies the back‑off behavior. These gaps mean the task’s deliverables are not fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

