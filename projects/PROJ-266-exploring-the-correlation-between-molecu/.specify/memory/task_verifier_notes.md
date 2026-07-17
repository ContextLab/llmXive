# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `tests/`, `data/`) is provided; the response contains only specification text and no actual project structure on disk. The task’s core deliverable is missing.
- **T003** — No linting or formatting configuration files (e.g., `setup.cfg`, `.flake8`, `pyproject.toml` with Black settings) or related documentation were provided. The evidence only contains a feature specification unrelated to configuring flake8/black, so the required artifact is missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No directories `data/raw/` or `data/processed/` and no checksum generation script or utility are present in the provided evidence; thus the required artifact is missing. The task’s core deliverable – a ready‑to‑use directory layout plus a checksum tool – has not been supplied.
- **T012** — The test file `tests/contract/test_dataset.py` exists, but it depends on `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`, which is missing, so the contract tests cannot be executed. The required schema artifact must be added (and contain the expected definitions) for the task to be satisfied.
