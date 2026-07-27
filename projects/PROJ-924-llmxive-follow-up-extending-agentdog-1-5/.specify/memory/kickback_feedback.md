# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The `pyproject.toml` file is present and contains a Black configuration, but the required `.ruff.toml` (or `ruff.toml`) file does not exist in the project directory, so the linting tool configuration is incomplete. The missing ruff configuration must be added to satisfy the task.
- `T012e` (rejected 1x): declared artifact(s) missing/empty/invalid: data/test/real_ground_truth_fixture.json
- `T011` (rejected 1x): No `config.py` file was presented in the evidence, nor any description of its contents. Without the file existing (or being shown) we cannot confirm that it manages random seeds, paths, and batch sizes as required. The implementer must add the `config.py` at the specified location with the appropriate configuration logic.
- `T012a` (rejected 1x): No evidence of a `data_loader.py` file containing `fetch_advbench` and `fetch_hf4` implementations was provided, nor any code showing they use `datasets.load_dataset` with streaming and avoid synthetic fallbacks. The required artifact is missing.
- `T015` (rejected 1x): No evidence was provided that a `checksums.json` file exists in the required `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` directory, nor any content showing raw data checksums. The implementer must add the non‑empty `checksums.json` file with appropriate checksum entries for the raw data.
- `T016b` (rejected 1x): No evidence of a modified `taxonomy_builder.py` containing `tracemalloc` monitoring or a RAM‑limit check is provided; the claim lacks any code, diff, or test output demonstrating the < 7 GB enforcement. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

