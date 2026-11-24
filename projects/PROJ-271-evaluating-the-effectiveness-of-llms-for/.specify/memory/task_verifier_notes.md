# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The evidence shows a `.flake8` file exists in `code/`, but its contents are not provided, so we cannot verify that it contains the exact required settings (`max-line-length = 88` and `ignore = E203,W503`). The implementer must supply the file’s content to confirm compliance.
- **T001c** — The evidence shows a top‑level `pyproject.toml` with the correct Black settings, and that a `pyproject.toml` file exists inside `code/`, but the content of `code/pyproject.toml` is not provided. Without confirming that the `code/pyproject.toml` contains the required `[tool.black]` section with `line-length = 88` and `target-version = ['py311']`, the task requirement is not satisfied. Provide the contents of `code/pyproject.toml` (or ensure it matches the specification).
- **T003** — Requested task execution failed; rerun successfully: code/verify_dataset.py exit=1
