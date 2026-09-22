# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The `code/main.py` does not contain a concrete runtime assertion that the pipeline runs without any 3D calls (it merely calls `assert_no_3d_calls("")` with an empty string) and it never invokes the T006 schema validators on `data/processed/descriptors.parquet`. Moreover, the required `data/processed/descriptors.parquet` file is missing entirely. These gaps mean the task’s requirements are not met.
- `T006` (rejected 1x): No `tests/contract/` directory or any schema validator files (e.g., JSON/YAML schemas, Python validation scripts) are present in the provided evidence. Consequently, the required artifact for setting up dataset and model output validators is missing.
- `T014c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors.parquet
- `T034a` (rejected 1x): No code, data, or result files were provided that compute or report the Jaccard similarity of the top feature clusters. The implementer supplied no artifact (e.g., script, notebook, CSV, or figure) containing the required similarity calculations, so the task’s core requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

