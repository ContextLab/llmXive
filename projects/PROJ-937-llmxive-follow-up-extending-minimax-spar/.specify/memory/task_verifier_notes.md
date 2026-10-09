# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The evidence does not show the existence of the required `data/raw` and `data/processed` directories in the project; no artifacts confirming these folders are present were provided. The implementer must create these two directories (non‑empty or placeholder files) at the project root.
- **T001c** — The evidence does not show the existence of the required `tests/unit` and `tests/integration` directories under the project root; no such paths were listed or confirmed by the collector. These directories must be present (even if empty) to satisfy task T001c.
- **T001d** — The evidence provided contains no confirmed artifact named `results` (or `results/` directory) under the project root `projects/PROJ-937-llmxive-follow-up-extending-minimax-spar`. Without a verified existence of the required `results` directory, the task is not satisfied. The implementer must add the `results` directory (even if empty) and ensure it is present in the repository.
- **T003** — The `pyproject.toml` with Black configuration exists at the repository root, but the `ruff.toml` is placed under `code/ruff.toml` instead of the repository root as the task explicitly requires. Move or copy `ruff.toml` to the top‑level directory (or create a duplicate there) to satisfy the specification.
- **T017d** — declared artifact(s) missing/empty/invalid: code/heuristics/selector.py
- **T032b** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T031** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
