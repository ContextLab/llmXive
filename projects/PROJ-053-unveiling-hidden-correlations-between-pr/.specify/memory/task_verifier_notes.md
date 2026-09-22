# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: data/processed/target_config.json, schema.yaml
- **T006** — The `schema_validator.py` file ends with an unfinished `except FileNotFoundError as fnf: log` line, which is a syntax error and prevents the module from running. Additionally, the required `contracts/dataset.schema.yaml` file is missing, so the validator cannot actually load a schema. These issues must be fixed for the task to be considered complete.
