# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The `code/utils/constants.py` file only contains a stub for lazy‑loading semantic proxies and does not define concrete constants such as `dark_mode` or `unread_count`. Moreover, the required source file `contracts/coverage.schema.yaml` is missing, so the code cannot actually read the `semantic_proxies` list. Both the data source and the expected constant definitions are absent.
- `T029` (rejected 1x): The implementer did not provide any artifact (e.g., a dataset file, script output, or documentation) showing a held‑out test set that excludes state variables present in the training‑time State Coverage Vector. No evidence of generation, contents, or verification of such a set is present, so the task requirement is unmet.
- `T036` (rejected 1x): No plot files or any other artifacts were provided in `data/processed/` (or elsewhere) showing a “Success Rate vs. Steps” visualization. The required output—a saved plot image or data file—simply does not exist, so the task is not satisfied.
- `T040` (rejected 1x): The submission contains no code, configuration, tests, or documentation that implements the required logic to flag “Invalid Proxy” when r < 0.3 nor any recommendation to expand the variable set. No artifact matching the task’s specification is present. The implementer must provide the actual implementation (e.g., function/module) and evidence (e.g., unit test, usage example) that the flagging behavior works as described.
- `T041` (rejected 1x): No code, configuration, tests, or documentation implementing “Proxy Validated” logging for the condition r ≥ 0.5 is present; the only provided material concerns an unrelated curriculum scheduler feature, so the required artifact is missing.
- `T044` (rejected 1x): No documentation files were provided in the `docs/` directory, nor any text explaining the scheduler trace as required by task T044. The implementer’s claim lacks the actual updated documentation artifact, so the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

