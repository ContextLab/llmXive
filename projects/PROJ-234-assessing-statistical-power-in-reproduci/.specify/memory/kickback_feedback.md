# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The required data file `data/processed/extracted_params.json` does not exist, and the contract schema `contracts/extracted_params.schema.yaml` is also missing. Without these artifacts the contract test cannot run or validate anything.
- `T030` (rejected 1x): The `tests/contract/test_schemas.py` test for the final report schema references `data/processed/audit_report.json` and `contracts/report.schema.yaml`, but both files are missing from the repository. Without these artifacts the contract test cannot run or validate anything, so the task requirement is not met.
- `T040` (rejected 1x): No evidence of `quickstart.md`, the `./run_pipeline.sh` execution, the generated `audit_report.md`, or a checksum comparison is provided. The required artifacts and verification steps are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

