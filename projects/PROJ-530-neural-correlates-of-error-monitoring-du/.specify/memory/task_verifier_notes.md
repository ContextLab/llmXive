# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The evidence provides only the project root path but no concrete files (e.g., `pyproject.toml`, `requirements.txt`, `environment.yml`, or similar) that declare a Python 3.11 project and list the required dependencies. Without such a manifest, we cannot verify that the specified packages are included, so the task is not satisfied.
- **T005** — The evidence contains no linting configuration artifacts (e.g., `.flake8`, `pyproject.toml` with Black settings, `setup.cfg`, or a pre‑commit hook) and provides no proof that flake8/black have been installed or run. Without these files or execution logs, the requirement to “Configure linting (flake8/black) and formatting tools” is not satisfied. Adding the appropriate config files and a demonstration of a successful lint/format run is needed.
- **T012** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
