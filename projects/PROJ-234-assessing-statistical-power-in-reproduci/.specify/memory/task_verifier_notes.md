# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The test script `tests/contract/test_schemas.py` is present, but the required artifacts `data/raw/openml_metadata_filtered.json` and `contracts/dataset_metadata.schema.yaml` do not exist, causing the test to be skipped or fail. Without these files the contract validation cannot be performed.
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/openml_metadata_filtered.json
- **T014** — declared artifact(s) missing/empty/invalid: data/raw/checksums.txt
- **T023** — No code, script, or documentation was provided showing that a DOI metadata API fallback is attempted when full‑text fetch fails, that the abstract is parsed with the same regexes, or that the source field is set to `"abstract"`. The required implementation artifact is missing.
- **T024** — The submission contains only the task description and specification excerpts; there is no code, JSON output, or log evidence showing that entries lacking extractable metrics are marked `"unparseable"` and that a warning is logged without crashing. The required artifact (implementation handling the edge case) is missing.
- **T026** — No artifact (e.g., a JSON/CSV file, database dump, or code that writes extracted records) was provided, and there is no evidence that the system actually saves each extracted record with the required fields. The implementer only supplied a feature specification without any concrete output.
- **T029** — The required unit test file `tests/unit/test_sensitivity.py` is missing from the repository, so no test code or results exist to verify the expected observed power and MDES values. Without the test artifact, the claim cannot be validated.
- **T030** — The provided `tests/contract/test_schemas.py` validates `data/raw/openml_metadata_filtered.json` against `contracts/dataset_metadata.schema.yaml`, not `data/processed/audit_report.json` against `contracts/report.schema.yaml`. Moreover, the required `data/processed/audit_report.json` and `contracts/report.schema.yaml` files are missing entirely. The task’s contract test and target artifacts are therefore not present.
