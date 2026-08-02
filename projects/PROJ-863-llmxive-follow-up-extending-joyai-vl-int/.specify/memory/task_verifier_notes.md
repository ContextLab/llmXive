# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file artifacts were provided showing that the required folders (`src/data_synthesis`, `src/feature_extraction`, `src/baseline`, `src/scheduler`, `tests/`) actually exist in the repository. Without concrete evidence of these paths, the task requirement is not satisfied. The implementer must add the project structure and show its presence (e.g., a directory tree or file list).
- **T003** — No linting (ruff) or formatting (black) configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black.toml`) or related setup scripts were provided; the evidence contains only the task description without any actual artifact. The required configuration artifacts are missing.
- **T004** — No pytest configuration files (e.g., `pytest.ini`, `conftest.py`) or marker definitions for CPU resource limits are present in the provided artifacts. Consequently, the requirement to set up pytest with CPU limit markers is not satisfied.
- **T009** — No artifact (e.g., a `.env` file, shell script, Dockerfile, or documentation) was provided that defines or sets the `JOYAI_VL_MODEL_PATH` and `DATA_SEED` environment variables, so the requirement to configure these variables is not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: src/data_synthesis/generator.py
- **T013a** — declared artifact(s) missing/empty/invalid: src/data_synthesis/verify_volume.py
- **T013b** — declared artifact(s) missing/empty/invalid: src/data_synthesis/handoff.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data_synthesis/visual_labeler.py
- **T015** — The provided artifacts discuss synthetic data generation, internal‑state feature extraction, and CPU‑optimized training, but contain no code, configuration, or documentation implementing deterministic velocity‑threshold rules for ambiguous events. No artifact addressing the “ambiguous events” requirement is present, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/manifest.jsonl
