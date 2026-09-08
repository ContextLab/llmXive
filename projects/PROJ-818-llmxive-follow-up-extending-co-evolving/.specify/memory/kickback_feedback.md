# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No files or code were presented in `tests/contract/` that define JSON schema validators for the `dataset`, `agent_state`, and `result` structures, nor any evidence that they were derived from the contracts in `contracts/`. The required validator artifacts are missing, so the task is not satisfied.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: src/generators/logic_generator.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/generators/grid_generator.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/generators/test_generator.py, data/test_instances.json
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/checksums.json
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/validate_dataset.py
- `T017` (rejected 1x): The required file `tests/unit/test_agent_conditions.py` does not exist, so no unit test for the bidirectional exchange logic is present. The task’s artifact is missing entirely.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/agents/sequential_agent.py
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: src/agents/mixed_agent.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

