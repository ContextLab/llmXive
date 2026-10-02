# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006a` (rejected 1x): The repository contains `code/data/preprocess.py`, but the script is only partially shown and there is no `data/processed/prompts.csv` file present. Since the required output file does not exist, the task of extracting COCO captions into that CSV has not been fulfilled. The next implementer must ensure the script runs successfully and creates a non‑empty `data/processed/prompts.csv`.
- `T006b` (rejected 1x): The repository contains the `code/data/preprocess.py` script, but the required output files `data/processed/prompts.csv`, `data/processed/prompts_train.csv`, and `data/processed/prompts_test.csv` are absent. No evidence (e.g., logs, timestamps, or generated CSV contents) shows that the script was actually run to produce these files. The task therefore remains unfinished.
- `T006d` (rejected 1x): The required output file `data/processed/diverse_prompts.csv` is missing; only the script `code/data/download_diverse_prompts.py` is present, with no evidence it was executed or produced the CSV. The task’s core artifact does not exist.
- `T022b` (rejected 1x): The required `data/processed/clustering_report.json` does not exist, and the provided `clustering.py` is incomplete (truncated) with no evidence that it was executed to produce the 16 rotation matrices. The task’s mandatory output is missing.
- `T028` (rejected 1x): The `load_matrices.py` script is present and implements loading/validation logic, but the required data file `data/processed/clustering_report.json` does not exist, so the script cannot actually load any rotation matrices. The missing JSON file means the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

