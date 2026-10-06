# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006d` (rejected 1x): The required artifact `data/processed/diverse_prompts.csv` is absent; therefore the script was not executed (or its output not saved), and the required columns and non‑empty captions cannot be verified. The next implementer must run `code/data/download_diverse_prompts.py` and ensure the CSV file is created with the specified columns and populated captions.
- `T023a` (rejected 1x): The provided `validate_clustering.py` file is truncated and contains only helper functions; it never checks whether `data/processed/clustering_report.json` exists nor invokes the validation logic. Additionally, the required `clustering_report.json` file is missing from the repository. The script must include a concrete existence check (and appropriate handling) and be a complete, runnable module.
- `T022` (rejected 1x): The required `data/processed/clustering_report.json` file is absent, so the deliverable cannot be verified. Additionally, there is no evidence that `clustering.py` was executed to produce the rotation matrices or that the JSON contains the required keys and matrix shape. The task needs the generated report file (with layers, subsets, boundaries, matrices 16×D) and confirmation that the script was run on the train‑split data.
- `T022c` (rejected 1x): The repository contains `code/run_quantization_validation.py`, but the required output `data/processed/quantized_activations.json` is absent, and there is no evidence that the script was executed or that it successfully used rotation matrices from T022. The task’s core deliverable is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

