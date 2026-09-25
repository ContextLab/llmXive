# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): I looked for the required directory tree under `projects/PROJ-344-the-impact-of-emotional-expression-in-ai/` (e.g., `data/raw`, `data/processed`, `data/features`, `code`, `tests/contract`, `tests/unit`, `tests/integration`, `outputs`, `state`) but no such folders or any listing of them were provided. The artifact confirming the project structure is missing.
- `T010` (rejected 1x): The required `contracts/dataset_schema.yaml` file is absent, so the test cannot load a real schema. Moreover, the provided `tests/contract/test_dataset_schema.py` is truncated (ends with an unfinished `assert SCH` line) and does not contain a complete validation test. Both the schema artifact and a functional test are missing.
- `T017` (rejected 1x): No code, documentation, or output files were provided that demonstrate the addition of logic to label all results as “associational only” (non‑causal). Without any artifact showing this framing, the requirement is not satisfied. The implementer must supply the modified analysis/reporting scripts or example output where the results are explicitly described as associational.
- `T020` (rejected 1x): No extraction or regression scripts, no output files (CSV, regression table, or figures) were provided, and there is no evidence of p‑values or pseudo R‑squared values being generated. Consequently the required artifact for User Story 2 is missing.
- `T021` (rejected 1x): No code, data files, regression output, or unified analysis report were provided; the claim lacks any tangible artifact demonstrating integration of regression results with consistency scores. The required deliverables (e.g., a report combining US1 consistency scores and regression findings, accompanying CSVs or figures) are missing.
- `T026a` (rejected 1x): declared artifact(s) missing/empty/invalid: code/run_pipeline.py
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: code/run_pipeline.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

