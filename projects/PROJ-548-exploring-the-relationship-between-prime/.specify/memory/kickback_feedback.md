# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listings were provided showing the required folders (`src/data/`, `src/analysis/`, `src/utils/`, `src/cli/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `data/results/`, `results/`, `state/`). Without concrete evidence that these paths exist, the task is not satisfied. The implementer must create and show the full project structure.
- `T003` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) nor any evidence that `ruff` and `black` were installed or integrated into the project. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- `T012` (rejected 1x): The provided `src/data/generate_primes.py` ends abruptly (truncated at `set_global_seed(confi`) and does not contain a complete pipeline that writes the required CSV, nor does it define the logic to stream results to `data/processed/primes_gaps.csv`. Moreover, the expected output file `data/processed/primes_gaps.csv` is missing entirely. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

