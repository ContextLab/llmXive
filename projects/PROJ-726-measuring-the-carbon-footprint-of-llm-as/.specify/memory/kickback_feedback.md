# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure was presented in the evidence; the response contains only the feature specification and no listing or screenshots of the required `code/`, `data/raw/`, `data/processed/`, `data/outputs/`, `tests/`, or `output/` folders. The implementer must provide proof that these directories exist in the repository root.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or CI workflow steps invoking ruff/black) or any other artifact demonstrating that linting and formatting tools have been set up are present. Without such files or scripts, the requirement to configure ruff and black is not satisfied. The next implementer should add the appropriate configuration files and ensure they are integrated into the project's workflow.
- `T004` (rejected 1x): No `download_data.py` file or its contents were provided; without the script fetching the CodeXGLUE Python code‑generation subset via the HuggingFace `datasets` library, the task requirement is unmet. The implementer must add the script with functional code that downloads the specified dataset.
- `T005` (rejected 1x): No evidence of a modified `download_data.py` is provided; the claim that fallback logic now avoids switching to HumanEval/MBPP, proceeds with a reduced sample size, logs the reason, or raises a clear error is unsupported. The required code changes and logging statements are missing.
- `T008` (rejected 1x): No evidence of a `download_data.py` file containing checksum validation was provided; the claim lacks any artifact (code, tests, or documentation) demonstrating that the checksum validation was implemented. The required implementation is therefore missing.
- `T011` (rejected 1x): No `run_inference.py` script is present, nor any JSON result containing the generated code string. The required artifact (a CPU‑only inference script loading GPT‑2‑medium and emitting the code string for LOC counting) is missing entirely.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

