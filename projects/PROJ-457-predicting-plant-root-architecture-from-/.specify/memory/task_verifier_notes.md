# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The task explicitly requires `pyproject.toml` with **Black & Flake8 settings**, but the file only contains `[tool.black]` (plus isort/pytest) — no Flake8 configuration section at all; Flake8 settings were moved entirely into `code/run_lint.py` command-line flags, which is not what was asked. Additionally, the recorded exit-0 run is vacuous ("No Python files are present to be formatted"), so there is no evidence the wrapper actually validates lint on real source files. Fix: add a Flake8 settings section (e.g. `[tool.flake8]` or documented equivalent) to `pyproject.toml` and demonstrate a non-tr
- **T006** — Requested task execution failed; rerun successfully: code/ingestion.py exit=1
