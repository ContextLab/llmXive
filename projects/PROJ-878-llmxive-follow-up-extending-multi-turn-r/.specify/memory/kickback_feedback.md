# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or screenshots were provided, so there is no evidence that the required folders (`data/raw/`, `data/processed/`, `code/`, `code/utils/`, `tests/`, `results/paper_figures/`) actually exist in the repository. The implementer must create these directories and show their presence (e.g., via a file tree or `ls` output).
- `T002` (rejected 1x): No evidence was provided showing that `__init__.py` files exist in the `code/`, `code/utils/`, or `tests/` directories; the claim lacks the required artifacts. The implementer must add these three files (non‑empty) to satisfy the task.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` entries for Black, a `.ruff.toml` or `ruff.toml`, or related setup scripts) were presented, nor any evidence that ruff and black have been integrated into the project’s workflow. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- `T008` (rejected 1x): No configuration file, script, or documentation defining the required environment variables (e.g., `RANDOM_SEED`, `MODEL_PATH`, etc.) is present. The claim provides no artifact that sets or documents these variables, so the task’s core deliverable is missing.
- `T013` (rejected 1x): The submission contains only a high‑level feature description and user stories; there is no code, script, or data implementing the required stratified orthogonalization with a rejection‑sampling loop, nor any log or output showing that the |r| < 0.2 constraint was enforced or that a final correlation coefficient was verified and recorded. The necessary artifact is missing.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/logical_puzzles.jsonl
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/logical_puzzles.jsonl, data/checksums.txt

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

