# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The `requirements.txt` file is present, but it lists the required packages without any version pins (e.g., `requests` instead of `requests==X.Y.Z`) and adds unrelated tooling entries, violating the task’s explicit demand for a pinned‑version requirements file.
- **T005** — The only artifact provided is the `requirements.txt` file; there is no evidence of a created virtual environment (e.g., a `venv/` directory, activation scripts, or a `pyproject.toml`/`Pipfile.lock`) nor any proof that the listed dependencies were installed (e.g., `pip freeze` output, installation logs, or a test import script). The task’s core requirement—creating a virtual environment and installing the dependencies—is therefore unmet.
