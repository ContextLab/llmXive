# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012a` (rejected 1x): No `data_loader.py` containing `fetch_advbench` and `fetch_hf4` implementations is provided, nor any test output showing `test_data_loader.py` passing. Consequently the required functions, error handling, and streaming behavior are not demonstrated.
- `T012c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/test_static_logs.json
- `T011` (rejected 1x): No `config.py` file was presented in the provided evidence, and thus we cannot verify that it exists or contains the required constants (`RANDOM_SEED=42`, `MAX_RAM_GB=7`, `BATCH_SIZE=64`). The implementer must supply the actual file (and optionally the passing pytest results) for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

