# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No evidence of the required `data/raw/`, `data/processed/`, and `data/results/` directories or their `.gitkeep` files is provided; the claim is unsupported by any tangible artifacts. The implementer must create the directories and include non‑empty `.gitkeep` files, then show their presence (e.g., a directory listing).
- **T039** — No evidence of the `specs/001-predicting-the-yield-strength-of-steel-a/spec.md` file or its updated Assumptions section is provided; without the actual file content we cannot verify that the resource limits were aligned with Constitution VI and the contradiction resolved. The required artifact is missing.
- **T009** — The `tests/contract/test_data_schema.py` file is truncated and ends with an unfinished assertion, and the required schema file `contracts/dataset.schema.yaml` is missing entirely, so the contract test cannot actually validate against the schema. Both the test implementation and the referenced schema artifact are absent/incomplete.
- **T010** — The integration test file exists, but it relies on `contracts/dataset.schema.yaml`, which is absent, so the test cannot perform the required schema validation. Additionally, the test code is truncated (e.g., unfinished type‑check logic), indicating it is not a complete, functional artifact. The missing schema file must be added (and the test code completed) for the task to be satisfied.
- **T011** — The required file `src/data/ingest.py` is missing entirely, so no code exists to fetch real data or clean missing yield strength rows. The task’s core deliverable is absent.
- **T012** — declared artifact(s) missing/empty/invalid: src/data/ingest.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/features.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/features.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data/ingest.py, data/raw/literature_mined.csv
- **T016** — declared artifact(s) missing/empty/invalid: src/data/features.py
- **T017** — The test file `tests/contract/test_model_output.py` exists, but the required schema file `contracts/output.schema.yaml` is missing, so the test cannot actually validate the model output against the contract. The missing schema must be added for the task to be complete.
- **T019** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T020** — declared artifact(s) missing/empty/invalid: src/models/train.py
