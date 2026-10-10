# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/` directory contains many source files instead of being empty with only a `.gitkeep`, and the required `logs/` directory (with a `.gitkeep`) is missing entirely.
- **T002** — The provided `requirements.txt` includes `scikit-learn`, which the task explicitly required to be removed; thus the dependency list does not match the specification. The file must be edited to contain only the listed packages (`numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `pytest`, `statsmodels`) and omit `scikit-learn`.
- **T003** — The repository contains a `pyproject.toml` with a Black configuration, but there is no `setup.cfg` and the `pyproject.toml` lacks any Flake8 (or other linting) settings. The task requires configuring both linting (Flake8) and formatting tools, which is not satisfied. Adding a Flake8 section (e.g., `[tool.flake8]` with desired options) to either `setup.cfg` or `pyproject.toml` would be needed.
- **T004** — The provided `code/config.py` exists and defines most required constants, but it does **not** expose a top‑level constant named `SEED_BASE` set to 42 as the task specifies (it only uses a local `seed_base` variable inside `get_simulation_grid`). Consequently the required `SEED_BASE=42` parameter is missing. Adding `SEED_BASE = 42` (or renaming the existing variable) would satisfy the task.
- **T027-4** — declared artifact(s) missing/empty/invalid: data/processed/regression_results.json
- **T039** — declared artifact(s) missing/empty/invalid: code/checkpoint_runner.py
