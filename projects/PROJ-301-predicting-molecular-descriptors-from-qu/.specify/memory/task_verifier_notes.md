# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows the required top‑level directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, and `docs/` each contain a `.gitkeep` file, but there is **no separate top‑level `utils/` directory**—the only `utils/` found is nested inside `code/`. The task explicitly requires a top‑level `utils/` folder, so the directory tree is incomplete.
- **T002** — The `requirements.txt` contains the required ten pinned packages, but it also includes two additional lines (`ruff==0.4.0` and `black==24.0.0`) that were not part of the task specification, so the file’s content does not exactly match the requested list.
- **T003** — Requested task execution failed; rerun successfully: code/run_lint.py exit=1
