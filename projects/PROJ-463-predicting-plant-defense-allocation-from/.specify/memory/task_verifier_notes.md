# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003a** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) are present in the provided artifacts, and the only evidence relates to a completely different feature (plant‑defense data pipeline). Consequently the task of configuring ruff and black has not been delivered.
- **T003b** — No installation scripts for HISAT2, fastp, or featureCounts are present, nor any logs or commands showing they were run and that the binaries are now in the system PATH. The required artifacts (script files and execution evidence) are missing.
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logger.py, src/utils/provenance.py
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/schemas.py
- **T007** — No evidence of the required directories (`data/raw`, `data/processed`, `data/traits`, `data/manifests`, `data/synthetic`) being created is present; the provided artifacts contain only task description and specifications, with no filesystem listing or files showing the directory structure. The implementer must add the requested folder hierarchy to the repository.
- **T011** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data/synthetic_generator.py, data/manifests/synthetic_manifest.json
- **T012a** — declared artifact(s) missing/empty/invalid: src/data/preprocess_fastp.py
