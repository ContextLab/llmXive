# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/` directory or an `__init__.py` file was presented; the claim lacks any tangible artifact confirming the root project structure was created.
- `T003` (rejected 1x): The claim provides only a statistical‑validity feature specification and no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black` settings, or a `pre‑commit` hook). Since there is no artifact showing that ruff and black have been set up, the requirement to configure linting (ruff) and formatting (black) tools is not satisfied. The missing artifacts need to be added for the task to be considered complete.
- `T004` (rejected 1x): No `data_loader.py` file or any code implementing dataset fetching with retry logic is provided; the evidence contains only the task description and project requirements, without the required artifact. Consequently, the implementation cannot be verified as completed.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): No `data_loader.py` file with added validation logic is present, nor any logs or tests demonstrating schema enforcement or warnings for zero‑relevance queries. The required code artifact is missing, so the task is not satisfied.
- `T007` (rejected 1x): No `config.py` file or its contents are present in the provided evidence; therefore the required constants for seeds, permutation count (N=1000), batch sizes, and memory thresholds have not been supplied. The task remains undone until a non‑empty `config.py` with those definitions is added.
- `T008` (rejected 1x): No `metrics.py` file or any code implementing a CPU‑only NDCG@k function with IDCG normalization and explicit relevance‑label mapping was presented. The required artifact is missing, so the task is not satisfied.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: results/p_values/raw_p_values.csv
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: results/mdes/mdes_summary.csv
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: results/sensitivity/alpha_sweep.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

