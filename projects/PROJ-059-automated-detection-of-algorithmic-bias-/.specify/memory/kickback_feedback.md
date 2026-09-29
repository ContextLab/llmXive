# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`src/bias_pipeline`, `src/cli`, `data/raw`, `data/processed`, `data/validation`, `tests/unit`, `tests/integration`, `state`) is presented; without visible artifacts the claim cannot be confirmed. The implementer must provide a listing or screenshots showing the created project structure.
- `T003` (rejected 1x): No configuration files (e.g., pyproject.toml, .ruff.toml, .pre-commit-config.yaml) or any other evidence of ruff and black being set up are provided; without such artifacts the claim that linting/formatting tools are configured cannot be verified.
- `T006` (rejected 1x): No evidence was presented showing that a `data/` directory with the subfolders `raw`, `processed`, and `validation` actually exists; the claim is unsubstantiated. The required directory structure must be created and verified (e.g., via a file listing) to satisfy the task.
- `T007` (rejected 1x): The `lexicon.py` file exists but its `load_lexicon` function only attempts to read a local CSV and raises an error if the file is absent; there is no implemented fallback to fetch from a verified HuggingFace URL. Moreover, the required `data/raw/lexicon.csv` file is missing from the repository. Consequently, the module cannot fulfill the task of loading the curated demographic lexicon as specified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

