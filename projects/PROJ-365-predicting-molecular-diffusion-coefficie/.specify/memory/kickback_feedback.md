# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006e` (rejected 1x): No `monitor.py` file or modified version is presented, and there is no JSON report showing a `"peak_memory_mb"` field. Without the actual code change or output artifact, the requirement to extend `monitor.py` cannot be verified as fulfilled.
- `T007b` (rejected 1x): No ingestion script, featurized JSONL output, training script, model files, or evaluation report are present. The claim provides only a textual description of the intended functionality, but the required artifacts (code, data files, and result metrics) are missing, so the task is not satisfied.
- `T012` (rejected 1x): The repository contains `code/ingestion/ingest.py`, which appears to implement the ingestion logic, but the required output artifact `data/processed/featurized.jsonl` is absent. Since the task explicitly demands that the pipeline write this JSONL file, the missing file means the implementation does not satisfy the requirement. The next implementer should ensure the script runs successfully on a sample CSV and produces a non‑empty `featurized.jsonl` at the specified location.
- `T015` (rejected 1x): The test file `tests/contract/test_featurization.py` is present, but the referenced schema `specs/001-predicting-molecular-diffusion-coefficie/contracts/dataset.schema.yaml` does not exist, so the contract test cannot actually perform validation. Add the missing `dataset.schema.yaml` (or correct the path) to satisfy the requirement.
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/evaluation.json
- `T027` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/sensitivity_summary.md
- `T035` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/resource_summary.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

