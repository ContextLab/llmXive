# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings, screenshots, or file‑tree output were provided to demonstrate that the required folders (`code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/`, `state/`) actually exist; without such evidence the claim cannot be verified.
- `T008` (rejected 1x): The claim provides only the task description and feature specifications; there is no evidence of a `tests/` directory, nor any `tests/unit` or `tests/integration` subfolders, nor any pytest configuration or test files. The required pytest framework and directory structure are missing.
- `T013` (rejected 1x): No `ingest.py` script (or any code) was presented; the evidence contains only the task description and project specifications, with no actual implementation that validates and excludes records lacking explicit degradation pathway labels. The required artifact is missing, so the task is not satisfied.
- `T015` (rejected 1x): No `preprocess.py` script or any code implementing SMILES‑based polyester detection was provided, nor any example input/output showing that non‑polyester records are filtered out. Without the actual artifact, the requirement cannot be verified.
- `T017` (rejected 1x): The required input file `data/processed/processed_graph_dataset.csv` is missing, so no statistical power analysis could be performed and no output artifact (e.g., report or results) is present. The task’s core requirement is therefore unmet.
- `T018` (rejected 1x): The implementer supplied no code, script, or configuration that implements the required subsampling logic based on `state/augmentation_trigger.json`. There is no artifact showing how the system checks for `action: "none"` when `n > 150`, so the task requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

