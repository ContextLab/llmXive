# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The provided `requirements.txt` lists the required packages but uses “>=” version specifiers instead of pinned “==” versions, and it also contains many additional packages that were not part of the task. Hence it does not satisfy the requirement to create a requirements file with pinned versions for the specified nine libraries.
- **T002** — No evidence of a Python 3.11 virtual environment (e.g., a `venv/` directory, `pyproject.toml`, or `requirements.txt`) or of installed dependencies is present; the claim cannot be verified from any provided artifact. The required environment setup files are missing.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or associated setup scripts) are present in the provided artifacts, so the requirement to configure ruff/flake8 and Black is not satisfied.
- **T025** — Requested task execution failed; rerun successfully: code/generate_report.py exit=1
