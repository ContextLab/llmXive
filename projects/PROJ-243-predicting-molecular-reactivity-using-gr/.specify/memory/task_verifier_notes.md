# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence provided does not show the six required directories (`data/raw`, `data/processed`, `data/assets`, `code`, `artifacts`, `tests`) nor the `.gitkeep` files inside each; no file listings or directory structures were supplied to confirm they exist. The implementer must add these directories with a `.gitkeep` file in each and provide evidence (e.g., `git ls-files` output) that they are tracked.
- **T002** — The repository contains `requirements.txt`, `pyproject.toml`, and `ruff.toml`, but the required `.flake8` file is missing, and there is no evidence (e.g., command output or logs) that `pip install -r requirements.txt`, `ruff check .`, or `black --check .` actually succeeded.
- **T003** — declared artifact(s) missing/empty/invalid: data/raw/checksums_schema.yaml, data/raw/checksums.json
- **T004** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
