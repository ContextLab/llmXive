# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` file exists and contains all the required pinned dependencies, but there is no provided evidence (e.g., install logs, command output, or test results) showing that `pip install -r requirements.txt` actually runs successfully without version conflicts. Adding such verification output is needed to satisfy the task.
- **T003** — The evidence contains no linting configuration files (e.g., `pyproject.toml`, `.flake8`, `.isort.cfg`) nor any recorded output showing `black --check .`, `flake8 .`, or `isort --check-only .` returning exit code 0. Without these artifacts or execution logs, the requirement to configure and verify linting/formatting cannot be confirmed.
