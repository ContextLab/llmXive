# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The `src/` directory exists, but the required `src/models/` subdirectory is reported as missing, so the specified directory structure is not fully present. Create the `models/` subdirectory under `src/` to satisfy the task.
- **T002** — declared artifact(s) missing/empty/invalid: src/lib/utils.py
- **T004** — The required `config/config.yaml` file is missing, and `src/config.py` neither loads a YAML file nor validates the configuration with the `jsonschema` library; its schema handling and structure also do not match the task’s specified `paths`, `seeds`, and optional `api_keys` dict contract.
- **T008** — declared artifact(s) missing/empty/invalid: scripts/checksum_raw_data.py, data/raw/, data/checksums.txt
- **T023** — Requested task execution failed; rerun successfully: src/models/train.py exit=1; src/cli/run_pipeline.py exit=2
- **T022** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T022b** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T025b** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py, data/processed/climate_overlap_check.json
- **T024** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/climate_overlap_check.json
- **T024a** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py
- **T039** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T040** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T042** — declared artifact(s) missing/empty/invalid: src/models/train.py, data/processed/training_log.txt
- **T028** — declared artifact(s) missing/empty/invalid: src/models/sensitivity.py
- **T029** — declared artifact(s) missing/empty/invalid: src/models/sensitivity.py
- **T043** — declared artifact(s) missing/empty/invalid: src/models/sensitivity.py
