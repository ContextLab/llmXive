# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory tree (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/` with subfolders `data/raw`, `data/processed`, `artifacts/figures`, `artifacts/logs`, `code`, `tests`) is provided; the claim cannot be verified without those actual folders. The implementer must create and show the directory structure.
- `T001b` (rejected 1x): No evidence of the required `projects/PROJ-484-the-impact-of-visual-attention-on-recall/.gitignore` and `README.md` files is provided, nor any content showing they contain the specified exclusions and minimal README text. The implementer must supply these two files with the correct entries.
- `T002` (rejected 1x): The required file `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/requirements.txt` does not exist, so the task’s specified artifact is missing despite a similar `code/requirements.txt` being present elsewhere. The correct location must contain the pinned dependencies.
- `T002b` (rejected 1x): No evidence of a `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/venv` directory or any output confirming that `code/venv/bin/python` reports Python 3.11.x is provided. The required virtual environment and its verification are missing.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T004` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `artifacts/figures/`, `artifacts/logs/`) is provided; the claim lacks any artifact listing or screenshots confirming their creation. The implementer must create and show the directory structure.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: code/config.py
- `T017` (rejected 1x): The required output file `data/processed/analysis.csv` does not exist, and the provided `code/preprocess.py` snippet shows only helper functions with no logic that writes or validates the final analysis‑ready CSV. Consequently the task of generating the CSV with schema validation is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

