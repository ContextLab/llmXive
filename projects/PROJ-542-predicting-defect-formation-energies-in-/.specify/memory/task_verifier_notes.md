# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — Checked `contracts/features.schema.yaml` and its validation test `code/tests/test_features_schema.py`. The schema defines columns named `A_atomic_radius`, `B_atomic_radius`, etc., whereas the task explicitly requires columns named `A_radius`, `B_radius`, etc.; the column naming does not match the specification, so the required schema is not correctly defined.
- **T001** — The required source files (`code/quickstart.md`, `code/pipeline/run.py`, `code/data/download.py`, `code/data/featurize.py`) are all missing, and the existing unit test imports `src.pipeline.run` (wrong module path) and checks that `run()` returns `None` instead of a dict with `raw_path`, `features_path`, and `model_path`. The task’s core artifacts and verification criteria are therefore not satisfied.
- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
