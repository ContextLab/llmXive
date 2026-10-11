# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b-schema** — declared artifact(s) missing/empty/invalid: contracts/config_schema.schema.yaml
- **T004** — The required schema file `contracts/config_schema.schema.yaml` is missing, and `code/config.py` validates against a different (non‑existent) schema path `contracts/simulation_config.schema.yaml` instead of the specified `contracts/config_schema.schema.yaml`. Consequently the loader cannot perform the required validation.
- **T004b-populate** — Checked `code/config.yaml`; while it includes `seed: 42` and `n_replications: 10000`, it lacks the required keys `use_real_data` and `use_streaming`, and the `dependency_strengths` list does not match `[0.0, 0.1, 0.2, 0.3, 0.5]` (it has a different field name and values). The task’s specification is not fully satisfied.
- **T005a** — The provided `contracts/dataset_schema.schema.yaml` defines fields like `file_path`, `checksum`, `sample_size`, and `variable_types`, but it does **not** include the required `variable_names` (with continuous/categorical options), `target_column`, or `data_type` fields, nor does it match the exact schema specification requested. The task’s required fields are missing or incorrectly named.
- **T006e** — declared artifact(s) missing/empty/invalid: code/sweep_config.yaml
- **T016-exec-us1** — declared artifact(s) missing/empty/invalid: results/logistic_models_us1.pkl
- **T016-exec-us2** — declared artifact(s) missing/empty/invalid: results/logistic_models_us2.pkl
- **T034** — Requested task execution failed; rerun successfully: code/quickstart_validation.py exit=1
- **T064** — declared artifact(s) missing/empty/invalid: results/config_audit.json
- **T064b** — declared artifact(s) missing/empty/invalid: data/dependency_manifest.yaml
