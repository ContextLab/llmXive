# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `projects/PROJ-428-evaluating-the-impact-of-outlier-removal/` directory (or any subfolders/files) is provided; the implementer did not supply the project structure or any contents, so the task is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black/Ruff settings, or CI scripts) are present, and the provided evidence only describes unrelated data‑analysis user stories. The required artifacts to configure flake8/ruff/black are missing.
- **T005** — No evidence of the required directory hierarchy (`data/raw/`, `data/processed/`, `data/results/`, `state/`) or a script that creates them atomically with `mkdir -p` was provided. The implementer’s claim cannot be verified because the artifacts are missing.
- **T011** — No evidence of the required files is present: there are no `data/raw/uci_*.csv` downloads, no `data/processed/uci_clean_*.csv` outputs containing identified continuous variables and baseline variance values, and no code or logs showing the processing steps. The task’s deliverables are missing.
- **T011b** — No evidence of the required CSV files in `data/raw/` nor the JSON file in `state/` was provided; without these artifacts the task of generating synthetic clean distributions with known variance parameters is not satisfied. The implementer must create and commit the `synthetic_clean_*.csv` files and the `synthetic_params.json` containing the ground‑truth parameters.
- **T013** — declared artifact(s) missing/empty/invalid: data/processed/injection_profile.json
