# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires creating the project directory structure (code, data/raw, data/derived, data/results, tests), but the evidence collector found no artifacts on disk — no directories or files were confirmed to exist at the project root. There is no evidence that `mkdir -p` was executed or that any of the five required directories exist; the implementer must actually create `projects/PROJ-421-assessing-the-impact-of-data-resolution-/` with its `code`, `data/raw`, `data/derived`, `data/results`, and `tests` subdirectories.
- **T003** — The directory listing confirms `.ruff.toml`, `.black.toml`, `setup_linting.sh`, and `pyproject.toml` exist in `projects/PROJ-421-.../code/`, but no file contents were provided, so there is no evidence the ruff/black configurations are actually valid or non-stub. Critically, `.black.toml` is not a configuration file Black recognizes (Black only reads `pyproject.toml`, or CLI flags), so the formatting tool is effectively unconfigured; the implementer should place Black settings under `[tool.black]` in `pyproject.toml` (or document CLI usage) and show the actual ruff config contents.
- **T039a** — declared artifact(s) missing/empty/invalid: projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/main.py
- **T014b** — declared artifact(s) missing/empty/invalid: projects/PROJ-assessing-the-impact-of-data-resolution-/code/resampling.py, data/derived/
- **T032a** — declared artifact(s) missing/empty/invalid: data/derived/sensitivity/
- **T039b** — declared artifact(s) missing/empty/invalid: code/main.py
