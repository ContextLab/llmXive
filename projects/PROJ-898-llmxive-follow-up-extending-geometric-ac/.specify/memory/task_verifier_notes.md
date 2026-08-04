# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The implementer provided only a feature specification and user stories; no file‑system evidence (e.g., a listing or screenshots) shows that `code/`, `data/`, and `tests/` directories actually exist or contain any files. Without concrete proof of those directories, the task requirement is not satisfied.
- **T001c** — No evidence of `.gitkeep` files in `data/raw`, `data/generated`, or `data/results` was provided; the required placeholder files are missing. The implementer must add a `.gitkeep` file to each of those three subdirectories.
- **T003** — The `ruff.toml` file is present and appears correctly configured, but the required `.pre-commit-config.yaml` file is missing from the repository. Without this file the task of configuring pre‑commit hooks for ruff/black is not fulfilled.
- **T004** — No evidence of the required `data/raw`, `data/generated`, `data/results` directories or accompanying `.gitkeep` files is provided; without visible artifacts we cannot confirm the directory structure was created. The implementer must add the directory tree and the placeholder `.gitkeep` files to satisfy the task.
- **T008** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
