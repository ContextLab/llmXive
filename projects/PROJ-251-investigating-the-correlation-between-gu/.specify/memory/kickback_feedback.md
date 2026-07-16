# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or other evidence were provided showing that the required folders (code/, data/raw, data/processed, data/results, specs/contracts/) actually exist; without such artifacts the claim cannot be verified. The implementer must create and show these directories (e.g., via a file tree or `ls` output) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings) are present in the provided evidence, so the task of configuring ruff/flake8 and black is not demonstrated.
- `T008` (rejected 1x): No `.env` file, configuration script, or documentation for loading API keys was provided. The claim lacks any tangible artifact demonstrating environment configuration management, so the requirement is not satisfied.
- `T011a` (rejected 1x): No `otutable.csv` or `metadata.csv` files from the HuggingFace dataset `biothings/srp053178_processed` are present, nor any script/code that performs the fetch. The required artifacts to demonstrate that Strategy A was implemented are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

