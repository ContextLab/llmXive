# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T001b** — Checked `projects/PROJ-190-investigating-the-relationship-between-b/requirements.txt`: the file exists but lists version constraints with `>=` (e.g., `numpy>=1.24.0`) instead of pinned exact versions (`==`), and therefore does not satisfy the task’s requirement for pinned versions of the specified packages.
- **T002b** — Checked the repository for any evidence of a Python 3.11 virtual environment (e.g., a `venv/` directory, `pyproject.toml`, `requirements.txt`, or activation scripts) and found none; the collector only listed the project root without any concrete artifact confirming that a virtual environment was created. The required artifact for task T002b is missing.
- **T003** — The evidence contains no linting or formatting configuration files (e.g., ruff, flake8, black settings, pre‑commit hooks) or any documentation that they have been set up; thus the required artifacts for task T003 are missing.
- **T014b** — Requested task execution failed; rerun successfully: code/data/verify_quality_run.py exit=1
