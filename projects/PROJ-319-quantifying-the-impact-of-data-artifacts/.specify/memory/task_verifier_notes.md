# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the listed directories (`code/`, `code/synthetic`, `code/metrics`, etc.) is provided; without a manifest, screenshot, or file‑tree showing these folders, we cannot confirm they were actually created. The implementer must supply concrete proof that the required project structure exists.
- **T001b** — No `.gitignore` file was presented; the evidence does not include the required file listing the specified exclusions, so the task’s deliverable is missing.
- **T001c** — No README.md file was presented; the required artifact is missing, so the task of initializing a README with project overview and quickstart instructions has not been fulfilled.
- **T003** — The implementer provided only the scientific feature specification and no linting/formatting configuration artifacts (e.g., `pyproject.toml` with Black and Ruff settings, a `.flake8` file, or documentation of tool integration). Consequently, the required linting and formatting setup is missing.
- **T006** — The repository contains `code/synthetic/generator.py`, but the shown code is truncated and provides no function that writes ground‑truth ellipticity/asymmetry to a JSON file. Moreover, the required `data/synthetic/gt_metadata.json` does not exist at all. Hence the task’s core requirement—saving exact ground‑truth values to a JSON metadata file—is not fulfilled.
- **T008** — No `tests/unit/` directory, test files, or pytest configuration (e.g., `pytest.ini` or `conftest.py`) are present in the provided evidence, so the required test structure and setup have not been delivered.
- **T009** — declared artifact(s) missing/empty/invalid: data/validation/validation_manifest.json
- **T015** — declared artifact(s) missing/empty/invalid: code/main.py, data/synthetic/gt_metadata.json
- **T022** — declared artifact(s) missing/empty/invalid: code/main.py, data/synthetic/gt_metadata.json
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/saturation_sweep.csv
