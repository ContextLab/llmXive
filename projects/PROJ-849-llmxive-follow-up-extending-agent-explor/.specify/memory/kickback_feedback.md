# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory `projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/` or any of its contents was provided; without a visible project structure the claim cannot be verified. The implementer must supply the actual folder and its files.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`) or related setup scripts are present in the provided artifacts. Consequently, the requirement to configure ruff/flake8 and Black has not been demonstrated. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/lib/config.py
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/lib/data_loader.py
- `T006` (rejected 1x): The required file `src/lib/tool_mapper.py` does not exist, so the functionality to load the JSON, extract per‑problem `tool_descriptions`, and raise `ERR_TOOL_MAPPING_MISSING` cannot be provided. The presence of the JSON mapping file alone does not satisfy the task. The missing module must be created with the specified behavior.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/lib/metrics.py
- `T008` (rejected 1x): No `tests/unit/` or `tests/contract/` directories with schema validation utilities are present in the provided evidence; the implementer did not supply any files, code, or directory listings demonstrating that the required structure and utilities have been created. The task therefore remains unfinished.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/services/retrieval_service.py, src/lib/tool_mapper.py
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: src/lib/data_loader.py, src/cli/run_diagnostic.py
- `T016#1` (rejected 1x): declared artifact(s) missing/empty/invalid: src/cli/run_diagnostic.py
- `T018` (rejected 1x): No code, configuration, or log files were provided showing that logging for the number of tools retrieved per problem and the embedding dimensions was added. The claim lacks any concrete artifact (e.g., modified source files, sample log output, or test results) to verify the required logging functionality.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

