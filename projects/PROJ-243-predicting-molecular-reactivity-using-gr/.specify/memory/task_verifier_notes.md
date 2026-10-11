# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt`, `pyproject.toml`, and `ruff.toml` files are present and correctly contain the required configurations, but the required `.flake8` file is missing from the project repository. Adding this linting configuration file is needed to satisfy the task.
- **T003** — The schema file exists and is valid YAML, but it does not describe the required structure: the task specifies fields `file_path` and `sha256`, whereas the schema defines `hash`, `file`, and `path` instead — the required field names are absent. Additionally, there is no evidence that `yamllint` was run and passed on the schema, which is the task's stated verification criterion. Fix: rewrite the schema to require `file_path` and `sha256` properties and provide yamllint execution output.
- **T004** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
