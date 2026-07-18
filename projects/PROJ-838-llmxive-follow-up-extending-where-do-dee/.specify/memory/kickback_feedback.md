# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `code/`, `data/`, and `tests/` directories is provided; the submission only contains a feature specification text and no actual project structure on disk. The task’s core deliverable—a populated folder hierarchy—is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with `ruff`/`black` settings, `.ruff.toml`, or CI scripts invoking these tools) are present, nor any evidence that the project has been set up to run ruff and black. The claim provides only unrelated feature specifications, so the required artifacts for task T003 are missing.
- `T007` (rejected 1x): The `code/downloader.py` file is incomplete (truncated, no download or checksum logic) and does not contain any code that actually fetches `HuggingFaceH4/tebench` or verifies a checksum. Moreover, the required `data/train.json` file is absent. Consequently, the task’s requirement to implement a downloader that retrieves and validates the dataset is not satisfied.
- `T008` (rejected 1x): No evidence was provided showing that `data/raw` and `data/processed` directories exist, nor that each contains a `.gitkeep` file. The required directory structure and placeholder files are missing from the artifacts.
- `T016` (rejected 1x): No code, tests, or documentation were provided showing that the parser now handles trajectories shorter than `int(len(spans) * config.cutoff_depth)` by using all spans, nor that it returns an empty graph for zero‑edge cases. The required implementation and verification artifacts are missing.
- `T017` (rejected 1x): No `save_graph` implementation is present in the repository, and there are no JSON files under `data/processed/graphs/` showing intermediate DAGs being saved. Without the function definition and its output artifacts, the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

