# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No `config.py` file was presented in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, nor any excerpt of its contents. Without the file (or its content) we cannot confirm that it manages random seeds, paths, and batch sizes as required. The implementer must add the file with the appropriate configuration definitions.
- `T005a` (rejected 1x): No `data_loader.py` file or its contents were provided, and there is no evidence that `fetch_advbench` and `fetch_hf4` have been implemented using `datasets.load_dataset` with streaming. The required functions are missing, so the task is not satisfied.
- `T008b` (rejected 1x): No `taxonomy_builder.py` file or modifications were presented, and there is no evidence of `tracemalloc`‑based memory monitoring, RAM‑limit enforcement, or exception handling. Without the required code artifact, the task’s requirement is not satisfied.
- `T013a` (rejected 1x): No `drift_scoring.py` file or `compute_cosine_distance` function was provided; without the actual code we cannot verify that the function calculates the minimum cosine distance to centroids as required. The implementer must add the file and implement the function accordingly.
- `T003` (rejected 1x): The `pyproject.toml` file is present and contains Black configuration, but the required `.ruff.toml` file is missing, so the linting tool (ruff) is not fully configured as the task demanded. The implementer must add a valid `.ruff.toml` with appropriate ruff settings.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

