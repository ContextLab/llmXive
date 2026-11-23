# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `code/specs/` subdirectory is missing; all other listed directories exist, but the absence of `code/specs/` means the task’s directory structure is not fully created.
- **T002** — The `code/` directory does not contain a `.gitignore` file at all, let alone one that lists the required exclusions (`data/raw/*`, `__pycache__`, `*.pyc`, `.env`, `*.pt`). The implementer must add this file with the specified patterns.
- **T003** — The `code/` directory contains placeholder files such as `.flake8` and `.pre-commit-config.yaml`, but no provided contents show that flake8 and black are actually configured (e.g., rule sets, black line length, pre‑commit hooks). Without the configuration details, we cannot confirm the linting/formatting tools are set up as required. Add the actual configuration file contents (or evidence of a successful lint/format run) to satisfy the task.
- **T004** — The `code/requirements.txt` file is present, but it lists the required packages without any version pins (e.g., `torch` instead of `torch==x.y.z`) and also contains extra packages (`datasets`, `pyarrow`, `rdkit`) that were not part of the task. The task explicitly required a requirements file with *pinned* versions for the ten specified libraries.
- **T005a** — Checked for `code/scripts/setup.sh` (required script) and `code/venv/` (virtual environment directory); both are reported as missing, so the task’s required artifact does not exist.
- **T005b** — declared artifact(s) missing/empty/invalid: code/scripts/setup.sh
- **T009** — declared artifact(s) missing/empty/invalid: code/contracts/prediction_schema.yaml
- **T021** — declared artifact(s) missing/empty/invalid: code/tests/unit/test_models.py
