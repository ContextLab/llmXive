# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/cli/run_pipeline_download_test.py exit=2
- **T001a** — the task writes platform-owned path(s) inside the project: `state/setup_dirs_verified.json` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T004a** — declared artifact(s) missing/empty/invalid: ingest.schema.yaml
- **T004b** — declared artifact(s) missing/empty/invalid: dataset.schema.yaml
- **T005** — The `code/utils/validate_schemas.py` file exists and defines the required `validate` function, but the unit test `tests/unit/test_validate_schemas.py` fails (FileNotFoundError) because the referenced schema files (`ingest.schema.yaml` and `dataset.schema.yaml`) are missing, so the test does not successfully validate a compliant sample without raising. The missing schema artifacts must be added for the test to pass.
- **T006** — Requested task execution failed; rerun successfully: code/cli/run_pipeline.py exit=1
