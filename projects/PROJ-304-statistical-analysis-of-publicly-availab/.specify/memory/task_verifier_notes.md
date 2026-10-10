# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires creating the directory structure `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, but the evidence collector found no artifacts on disk — no directories (or placeholder files within them) were confirmed to exist at the project root. The implementer's claim of completion is unsupported by any observed directory structure; the next step is to actually create these directories (with appropriate marker files, e.g., `.gitkeep`, if the version control system requires them).
- **T003** — No artifacts were provided or confirmed on disk for this task — the collector explicitly notes the task references no code/data/figure path and no configuration files (e.g., `pyproject.toml`, `ruff.toml`, `.ruff.toml`, `black` config, or CI workflow) were shown to exist. There is no evidence that ruff and black are actually configured anywhere in the project.
- **T016** — Requested task execution failed; rerun successfully: code/harmonize_and_save.py exit=1
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
