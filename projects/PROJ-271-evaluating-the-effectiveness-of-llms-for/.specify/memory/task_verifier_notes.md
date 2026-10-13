# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The `.flake8` file is present in `code/`, but no evidence of its contents is provided, so we cannot confirm it sets `max-line-length = 88` and ignores `E203,W503` as required.
- **T001c** — The evidence shows a `pyproject.toml` file in the project root with the required Black settings, and a `pyproject.toml` entry listed inside `code/`, but the content of the `code/pyproject.toml` file is not provided. Without confirming that the `code/pyproject.toml` exists and contains the required `[tool.black]` settings (`line-length = 88`, `target-version = py311`), the task requirement is not demonstrably satisfied.
