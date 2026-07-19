# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was presented showing that the required `code/`, `data/raw`, `data/processed`, `results`, and `specs/` directories actually exist in the repository; the claim is unsupported. The implementer must provide a directory listing or screenshots confirming these folders are created.
- **T001b** — declared artifact(s) missing/empty/invalid: config.yaml
- **T002b** — No repository, script, or documentation showing that a git repository was initialized or that a Python virtual environment was created was provided; the claim lacks any tangible artifact to verify the required setup.
- **T003** — The only evidence presented concerns a research pipeline for static analysis tools and contains no configuration files, scripts, or documentation for ruff or black. There is no artifact (e.g., pyproject.toml, .ruff.toml, or black configuration) that demonstrates linting/formatting setup, so the required task is not satisfied.
- **T009** — No configuration-management code or `.env` handling script was presented; there is no artifact showing that GitHub tokens or paths are loaded from a `.env` file, so the task’s requirement is not satisfied.
- **T010** — No directory structure or checksum validation code for `data/raw` and `data/processed` was presented; the response contains no files, scripts, or documentation demonstrating that the required artifacts exist or function as specified.
- **T012** — declared artifact(s) missing/empty/invalid: code/tests/test_acquisition.py
- **T018** — No code, script, or documentation was provided showing added logic to detect repositories with zero merged PRs, skip them, log the event, or to catch and log tool execution failures. Without any artifact demonstrating these edge‑case handlers, the task requirement is not satisfied.
