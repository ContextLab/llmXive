# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T091` (rejected 1x): The required output file `data/processed/power_analysis_results.json` does not exist, and the provided script is incomplete (truncated) with no evidence that it generates the JSON containing `estimated_power`, `target_N`, and `method`. The task’s deliverable is therefore missing.
- `T004` (rejected 1x): The required verification script `code/verify_data_model.py` is missing, and there is no evidence that the markdown file `specs/001-the-impact-of-text-message-tone-on-perce/data-model.md` exists or contains the required headings. Without these artifacts, the task’s requirement is not satisfied.
- `T005` (rejected 1x): No directory listings, file tree, or .gitkeep files were provided, so we cannot confirm that `data/raw`, `data/processed`, and `data/consent` exist nor that each contains a `.gitkeep`. The implementer must show the actual filesystem state (e.g., output of `ls data/` and `ls data/*/`) to verify the required structure.
- `T006` (rejected 1x): The required schema files (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_ready.schema.yaml`, `lmm_summary.schema.yaml`, `analysis_result.schema.yaml`) are not present in the `specs/001-the-impact-of-text-message-tone-on-perce/contracts/` directory (the only schema listed, `schema.yaml`, is missing). Without these files the pytest contract tests cannot load and validate the schemas, so the task is not genuinely completed.
- `T015` (rejected 1x): The repository lacks the required `data/processed/presentation_orders.csv` file, and the provided `code/03_random_order.py` is incomplete (the `save_orders` function is cut off and no command‑line handling or entry‑point is shown). Consequently the script cannot generate the promised CSV, so the task’s requirement is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

