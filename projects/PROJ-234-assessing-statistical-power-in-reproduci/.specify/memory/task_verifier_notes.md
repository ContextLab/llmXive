# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The test references `data/raw/openml_metadata_filtered.json` and `contracts/dataset_metadata.schema.yaml`, but both files are absent from the repository. Without these required artifacts the contract test cannot perform the validation.
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/openml_metadata_filtered.json
- **T014** — declared artifact(s) missing/empty/invalid: data/raw/checksums.txt
- **T015** — The required artifact `data/ingest.log` does not exist, so no JSON extraction statistics are logged as specified. The implementer must create the `data/ingest.log` file with the appropriate JSON content.
- **T016** — No code, test, or documentation was provided that shows a check for duplicate IDs and the raising of a `ValueError` when any remain after resolution. The required artifact (implementation of the duplicate‑ID validation logic) is missing, so the task is not satisfied.
- **T019** — The required `data/processed/extracted_params.json` file does not exist, and the schema `contracts/extracted_params.schema.yaml` is also missing. Moreover, the provided `tests/contract/test_schemas.py` snippet is truncated and does not show a `test_extracted_params_schema` implementation, so the contract test cannot actually validate the missing artifacts. These essential artifacts must be created and the test completed for the task to be considered done.
- **T032** — No code, script, or test output was provided that shows entries with `metric_type "F"` are converted to Cohen’s d, that power values are clamped to ≤ 1.0, or that a warning is logged. The required implementation artifact is missing.
- **T035** — No `audit_report.md` file or its contents were provided, and there is no evidence that a mandatory disclaimer was appended to the end of such a file. The required artifact is missing, so the task is not satisfied.
- **T037** — The required file `data/processed/audit_report.md` does not exist, so the final audit report was not assembled as specified. The task’s primary deliverable is missing.
- **T040** — No evidence of `quickstart.md`, the `./run_pipeline.sh` execution, the generated `audit_report.md`, or a checksum comparison is provided. The required artifacts and verification steps are missing, so the task is not satisfied.
