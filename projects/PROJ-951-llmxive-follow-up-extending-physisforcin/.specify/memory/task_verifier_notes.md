# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/` was presented or listed in the provided artifacts, so the required project root directories are missing.
- **T001b** — No directory listings or other evidence were provided showing that `src/`, `tests/`, and `data/` actually exist under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`. Without concrete proof of these subdirectories, the task requirement is not satisfied.
- **T002** — No repository, `pyproject.toml`, `requirements.txt`, or any code files initializing a Python project with the listed CPU‑only packages are present. The implementer provided only a feature specification; the required project setup artifacts are missing.
- **T003** — The implementer supplied only a high‑level feature specification for a physics‑filter pipeline and no linting/formatting configuration files, scripts, or CI integration. There is no evidence of ruff or black being set up (e.g., no `pyproject.toml`, `.ruff.toml`, or pre‑commit hooks), so the task “Configure linting (ruff) and formatting (black) tools” is not satisfied. The missing artifacts are the actual configuration and integration of ruff and black in the project.
- **T012** — declared artifact(s) missing/empty/invalid: data/prompts.jsonl
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T007** — declared artifact(s) missing/empty/invalid: src/training/config.py
- **T007b** — The required `config.yaml` file does not exist on disk, so the schema definition for `filter_discard_percent` and other required keys was never provided. The implementer must add a non‑empty `config.yaml` containing the appropriate schema.
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/verify_env.py
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/seeding.py
- **T006b** — declared artifact(s) missing/empty/invalid: src/utils/profile_memory.py
