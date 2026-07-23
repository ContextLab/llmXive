# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — I could find no evidence of the required directory tree under `projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/` nor the empty `__init__.py` files in `code/` and `tests/`. The implementer’s claim cannot be confirmed because the necessary folders and files are missing.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The test function `test_dataset_schema_validation` is present and correctly uses `jsonschema.validate`, but the required schema file `specs/001-predict-carbon-diffusion-bcc/contracts/dataset.schema.yaml` is missing, so the test cannot actually perform validation. Add the missing schema file with the proper definition.
- **T014** — The `tests/test_contracts.py` file correctly implements `test_model_output_schema_validation` using `jsonschema.validate`, but the required schema file `specs/001-predict-carbon-diffusion-bcc/contracts/model_output.schema.yaml` is missing, so the test cannot actually validate `model_results.json` against the intended schema. Add the missing schema file (with the definition from T005) to complete the task.
- **T022** — No code files, commit history, or refactored scripts were presented; there is no evidence of any cleanup or readability improvements for the diffusion‑prediction project. Consequently the required artifact (refactored, readable code) is missing.
- **T023** — No evidence of a final validation artifact (e.g., a checksum report, contract verification script, or log confirming all contracts and checksums have been validated) is present; the implementer provided only the feature specification without any concrete validation output.
- **T024** — No `quickstart.md` validation artifact (e.g., a log, report, or script output) is present; the implementer provided no evidence that the quickstart guide was executed and verified end‑to‑end reproducibility. The required validation output is missing.
