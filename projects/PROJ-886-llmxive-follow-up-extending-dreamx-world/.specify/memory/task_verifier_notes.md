# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000a** — declared artifact(s) missing/empty/invalid: scripts/config_cpu_env.sh
- **T001c** — The implementer supplied non‑empty `__init__.py` files (they contain imports and docstrings) and did not provide the required placeholder files `requirements.txt`, `README.md`, `pyproject.toml`, or `.ruff.toml` at all. The task demanded empty placeholder files for all listed paths, which is not satisfied.
- **T005a** — The provided `pyproject.toml` correctly contains the `[tool.black]` and `[tool.ruff]` sections, but the required `.ruff.toml` (or `ruff.toml`) file in `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/` is missing, so the linting configuration is incomplete.
- **T005b** — No linting logs, command output, or any proof that `ruff check` and `black --check` were run and passed without errors in the specified project directory were provided. The required artifact (successful linting verification) is missing.
