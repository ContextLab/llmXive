# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002e** — The required file at `projects/PROJ-402-the-impact-of-interoceptive-awareness-on/code/requirements.txt` does not exist; only a similarly named file at a different location is present. The task demands the file at the specific project path, so the implementation is incomplete.
- **T002b** — The required `projects/PROJ-402-the-impact-of-interoceptive-awareness-on/code/requirements.txt` file does not exist, and no `venv` directory is present, so dependencies could not be installed as specified. The task’s primary artifact is missing.
- **T002c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T002d** — The repository lacks the required `contracts/dataset.schema.yaml` file, so the validator cannot load the pre‑existing schema. Moreover, the provided `schema_validator.py` is truncated and does not clearly show the required return object `{valid, errors, checksum, behavioral_found}`, the specific phase‑vs‑behavioral task logic, or the exit‑code handling and checksum logging mandated by the task. Both the missing schema file and the incomplete implementation need to be added/fixed.
- **T008** — The required `conftest.py` file, which should contain the pytest configuration for random seed pinning, is missing from the repository. Without this file the test environment cannot enforce deterministic behavior, so the task’s core requirement is not satisfied.
