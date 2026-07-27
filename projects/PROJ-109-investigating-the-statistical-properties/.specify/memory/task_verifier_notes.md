# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The implementer provided only narrative user stories and no evidence of the required directories (`code/data`, `code/analysis`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`, `docs`). Since the artifact (the project folder hierarchy) is missing, the task is not satisfied.
- **T004** — declared artifact(s) missing/empty/invalid: code/config.py
- **T008** — The repository contains `code/data/synthetic_generator.py` with a fixed seed, the required concentration offset, and code to write an HDF5 file, but the expected output file `data/raw/synthetic_halos.h5` is absent, so the required artifact is missing.
- **T015** — The `preprocess.py` file imports `jsonschema` but never loads `halo.schema.yaml` nor calls `validate` on the filtered DataFrame; the code ends before any validation logic is added. Consequently, the required post‑filter validation against `code/contracts/halo.schema.yaml` is missing.
