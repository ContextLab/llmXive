# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that the required directories (`data/raw`, `data/processed`, `code/src`, `code/tests`, `code/notebooks`, `paper`, `state`, `contracts`) exist under `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/`. The implementer’s claim is unsubstantiated.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or related setup scripts) were presented for the `code/` directory, so we cannot verify that ruff/flake8 and Black have been configured. The required artifacts are missing.
- `T008b` (rejected 1x): I looked for the required pilot results (entropy‑convergence comparison for N=10) and for the baseline hypothesis document `paper/model_substitution_rationale.md`; neither the data nor the markdown file is present in the repository. Without these artifacts the task’s validation requirement is not satisfied.
- `T013` (rejected 1x): The provided `code/src/inference.py` only contains model loading and a stub `generate_solution` function; it does not show any loop over k = 1, 2, 3, no Docker sandbox execution, no comparison against the problem’s `test` field, and no recording of non‑convergence events. Moreover, there is no evidence that the file avoids reading `data/processed/entropy_results.csv`. The required iterative refinement logic is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

