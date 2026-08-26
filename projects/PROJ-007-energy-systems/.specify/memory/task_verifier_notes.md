# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence does not show any `src/`, `tests/`, `data/`, or `specs/` directories or files; no project structure is present to verify that the required folders were created. The implementer must add the specified directory hierarchy (and at least placeholder files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) are present, nor any documentation showing that ruff and black have been set up for the project. The required artifacts to prove the tools are configured are missing.
- **T004** — No `pytest` configuration file (e.g., `pytest.ini`, `conftest.py`) or `.gitignore` that excludes data artifacts is present in the provided evidence. Without these files, the task of setting up pytest and a proper .gitignore has not been fulfilled.
