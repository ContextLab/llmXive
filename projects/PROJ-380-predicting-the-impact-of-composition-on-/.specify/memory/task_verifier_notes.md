# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required project directories (`code/`, `data/`, `tests/`, `docs/`) is provided; the claim lacks any artifact showing that the structure was created. The implementer must add the missing folder hierarchy (and optionally placeholder files) to satisfy the task.
- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or integration scripts are present; therefore the required artifact for configuring ruff/flake8 and Black does not exist.
- **T005** — No `utils/config.py` file or its contents were presented, so there is no evidence that random seeds and path constants have been defined as required. The implementer must add the file with appropriate seed initializations and path constant definitions.
- **T006** — No `utils/provenance.py` file is present, nor any code showing checksum generation or recording to the required `state/projects/PROJ-380-...yaml` file. The evidence provided consists only of a project description, so the required implementation is missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — No evidence was provided that a `data/` directory (with subfolders `raw/`, `processed/`, and `artifacts/`) actually exists in the repository; the claim is unsupported by any listed files or screenshots. The required directory structure must be created and shown (e.g., via a directory tree listing).
- **T012a** — No `utils/provenance.py` file or any code implementing checksum recording logic is present in the provided artifacts; the only evidence relates to a shear‑modulus prediction pipeline, which does not address the required provenance checksum feature. The missing implementation must be added to `utils/provenance.py`.
- **T011** — declared artifact(s) missing/empty/invalid: code/data/synthetic_generator.py, data/raw/synthetic_bmg_seed.csv
