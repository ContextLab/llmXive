# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The contract test expects a schema at `contracts/dataset_metadata.schema.yaml`, but that file is missing, causing the test to fail. Additionally, the JSON data file is only a placeholder empty list, not real filtered metadata. Both required artifacts are absent or insufficient, so the task is not genuinely satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/openml_metadata_filtered.json
- **T014** — declared artifact(s) missing/empty/invalid: data/raw/checksums.txt
- **T015** — The required artifact `data/ingest.log` does not exist, so no JSON extraction statistics are logged as specified. The implementer must create the `data/ingest.log` file with the appropriate JSON content.
- **T016** — No code, test, or documentation was provided that shows a check for duplicate IDs and the raising of a `ValueError` when any remain after resolution. The required artifact (implementation of the duplicate‑ID validation logic) is missing, so the task is not satisfied.
- **T019** — The provided `tests/contract/test_schemas.py` contains a test for `openml_metadata_filtered.json` against `dataset_metadata.schema.yaml`, not the required `test_extracted_params_schema` for `data/processed/extracted_params.json`. Moreover, the `data/processed/extracted_params.json` file and the `contracts/extracted_params.schema.yaml` schema are both missing. The task’s required artifacts are absent, so the requirement is not satisfied.
- **T021** — The `code/02_parse_publications.py` file is truncated and does not contain the logic to iterate over the raw JSON, invoke the full‑text fetch, parse results, and write them to `data/processed/extracted_params.json`. Moreover, the required output file `data/processed/extracted_params.json` is absent. The implementation therefore does not fulfill the task’s requirements.
- **T022** — No code, script, or unit‑test files were provided that demonstrate fetching the full‑text with `requests.get`, invoking `oa_checker.is_open_access`, handling the paywalled case, or a mock‑based test verifying this behavior. The required artifacts are missing, so the task is not satisfied.
- **T027** — declared artifact(s) missing/empty/invalid: data/processed/extraction_stats.json
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/power_audit_results.json
- **T036** — declared artifact(s) missing/empty/invalid: data/processed/mdes_summary.json
