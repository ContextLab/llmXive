# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No evidence of a `.gitignore` file was found in the project root (`projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0`), nor any content showing it ignores large files and Python artifacts. The required artifact is missing.
- **T002a** — The `code/requirements.txt` file is present, but it lists the required packages without any version pinning (e.g., `torch-cpu` instead of `torch-cpu==X.Y.Z`). The task explicitly demanded pinned versions, so the artifact does not satisfy the requirement.
- **T002b** — No concrete artifact (e.g., a created virtual environment directory, a `requirements.txt`/`pyproject.toml` file, or a script/command log showing `python -m venv` and `pip install` execution) was found in the provided project tree. Without such evidence the claim that a Python 3.11 virtualenv was initialized and dependencies installed cannot be verified.
- **T003** — The evidence provides only the project root path but contains no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`, or CI scripts invoking ruff/flake8/black). Without these artifacts, the requirement to configure linting and formatting tools is not satisfied. Adding the appropriate configuration files and confirming they are present and non‑empty will be needed.
- **T004** — Checked the `data/` directory (exists with `__init__.py`, `city_list.txt`, `processed/`, `raw/`) and the top‑level `results/` directory. The required subdirectory `interim/` is missing, and `results/` is not placed under `data/` as the task specifies.
- **T005** — declared artifact(s) missing/empty/invalid: code/lib/alignment.py
- **T006** — declared artifact(s) missing/empty/invalid: code/lib/degradation.py
- **T007a** — declared artifact(s) missing/empty/invalid: code/lib/models.py
- **T007b** — declared artifact(s) missing/empty/invalid: code/lib/models.py
- **T007c** — declared artifact(s) missing/empty/invalid: code/lib/models.py
- **T007d** — declared artifact(s) missing/empty/invalid: code/lib/models.py
- **T008** — declared artifact(s) missing/empty/invalid: data/results/execution.log
- **T020** — declared artifact(s) missing/empty/invalid: code/lib/cpu_3dgs_wrapper.py
- **T028** — declared artifact(s) missing/empty/invalid: code/lib/metrics.py
- **T029** — declared artifact(s) missing/empty/invalid: code/lib/metrics.py
- **T029b** — declared artifact(s) missing/empty/invalid: code/lib/metrics.py
