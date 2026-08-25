# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The required `state/projects/PROJ-006-agriculture-optimization.yaml` file is missing, so the state cannot be updated with artifact hashes, and no evidence of a dry‑run hash calculation is provided. The `state_manager.py` exists, but without the YAML file (and verification) the task is not fully satisfied.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The repository lacks the required `contracts/dataset.schema.yaml` file, so the generator cannot be validated against the schema. Moreover, the provided `synthetic_generator.py` is truncated, contains undefined variables (e.g., `n`), and does not produce all required columns (latitude, longitude, extension_visits, etc.) nor include CI‑environment detection logic. The task therefore remains unfinished.
- **T010a** — The repository contains `src/cli/run_pipeline.py`, which appears to implement the required logic and flags, but the required workflow file `.github/workflows/ci.yml` is completely missing. Without this CI configuration the task is not fully satisfied.
- **T046** — The implementer did not provide any of the required test files (e.g., `tests/contract/...`, `tests/integration/...`, `tests/unit/...` for T013, T014, T023, T024, T028, T029). No skeleton files or directory structure is present, so the verification condition “assert files exist” cannot be satisfied. The task remains unfinished until those test files are created.
