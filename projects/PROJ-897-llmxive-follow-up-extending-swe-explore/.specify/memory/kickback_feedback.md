# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No dataset files, filtering scripts, or synthetic mutation code were supplied; therefore the required curated “hard” instance subset and generated ambiguous issues do not exist to verify the acceptance criteria. The implementer’s claim provides only a plan amendment, not the concrete artifacts the task demands.
- `T001` (rejected 1x): No directories such as `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/contract/`, `contracts/`, `docs/`, or `paper/` are present, nor any linting/formatting configuration files (e.g., `pyproject.toml` with ruff/flake8/black settings). The implementer provided no artifact evidence to confirm the required project structure or tool setup.
- `T032` (rejected 1x): The required `data/results/final_metrics.json` file does not exist, so there is nothing for `hash_artifacts.py` to hash; the integration cannot be verified. The missing final metrics file must be created (and then hashed) for the task to be considered complete.
- `T047` (rejected 1x): No code, tests, or documentation implementing deterministic loop detection and early‑exit logic were provided; the only evidence is the high‑level feature description, which does not constitute the required artifact. The implementer must supply the actual implementation (e.g., a function/module with deterministic loop detection and early‑exit behavior) and any associated verification artifacts.
- `T048` (rejected 1x): No code, scripts, or documentation implementing a “robust mutation fallback with hard fail” were provided; the only evidence is a high‑level feature specification unrelated to the required mutation fallback logic. The required artifact (implementation of the fallback mechanism) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

