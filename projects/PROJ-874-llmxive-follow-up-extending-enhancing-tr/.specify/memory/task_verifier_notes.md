# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b** — the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003** — The only evidence is a log claiming that `pyproject.toml`, `.ruff.toml`, and `.flake8` were written, but the actual configuration files are not present in the artifact list, nor is their content shown. Without the concrete config files, we cannot confirm that linting (ruff/flake8) and formatting (black) are truly configured. The missing configuration files need to be added and verified.
- **T013** — Requested task execution failed; rerun successfully: code/generate.py exit=1
