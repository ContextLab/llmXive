# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors.parquet
- `T019` (rejected 1x): The `code/main.py` only defines the validation functions and the file ends abruptly (e.g., `missing = r`), so the runtime assertions are not fully implemented nor invoked. Moreover, the required `data/processed/descriptors.parquet` file is absent, so the validation of its existence and contents cannot succeed. The task’s requirement is therefore not satisfied.
- `T032` (rejected 1x): The `code/models/interpret.py` file is present but its content is cut off (ends mid‑line) and thus does not constitute a complete implementation. Moreover, the required input `data/processed/descriptors.parquet` is missing entirely, so the module cannot perform the intended Cluster‑Aware SHAP analysis. Both the script and the necessary data artifact need to be provided/fixed.
- `T034a` (rejected 1x): No artifact (e.g., script, notebook, data file, or result table) showing the computed Jaccard similarity of top feature clusters across multiple bootstrap resamples is present; the claim provides only a description without any concrete output. The required evidence is missing.
- `T034b` (rejected 1x): The submission provides no code, data, or results showing that Jaccard similarity of top SHAP features across bootstrap resamples was computed; there is no artifact (script, output file, or figure) demonstrating compliance with spec SC‑003. Consequently the required deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

