# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003a** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) are present, nor any documentation showing that `ruff` and `black` have been set up for Python 3.11. The required artifacts to demonstrate the configuration are missing.
- **T003c** — declared artifact(s) missing/empty/invalid: data/manifests/env_validation.json
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/schemas.py
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/setup_dirs.py
- **T015** — The repository contains `src/data/synthetic_generator.py`, but the file is truncated and shows no logic that actually writes the TPM matrix or creates the required `data/manifests/synthetic_manifest.json`. Moreover, the manifest file is absent from the filesystem. The task’s core requirement—a manifest with the specified schema and checksums—is not satisfied.
