# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The claim provides no evidence of the required directories (`code/`, `tests/`, `data/raw`, `data/processed`) being present or populated; no file listings or screenshots are supplied. Without concrete artifacts showing the project structure, the task requirement is not satisfied.
- **T003** — The repository contains no linting or formatting configuration files (e.g., `.flake8`, `.pylintrc`, `pyproject.toml` with Black settings, or `isort.cfg`) and no evidence of these tools being set up in CI. To satisfy T003, the implementer must add the appropriate configuration files and ensure the tools run as part of the development workflow.
- **T011** — No `tests/integration/` directory or any test files were presented, and there are no mock FASTQ files or test code shown that would verify the pipeline flow. The required integration test scaffolding is missing entirely.
