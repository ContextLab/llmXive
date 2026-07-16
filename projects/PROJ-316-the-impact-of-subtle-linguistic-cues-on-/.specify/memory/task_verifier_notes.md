# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001c** — The `data/raw/rater_metadata.json` correctly contains the Cohen's Kappa metrics, but the required `data/processed/ratings.csv` file is missing, so the core deliverable of the task is not present. The pipeline cannot be considered complete until the ratings CSV with the specified columns is generated.
- **T002** — No directory structure or `__init__.py` files are presented in the provided evidence; the claim that the required folders (`src/`, `tests/`, `data/raw`, `data/processed`, `data/derived`, `code/`) and empty `__init__.py` files exist cannot be verified. The implementer must supply a concrete listing or screenshot showing these directories and files.
- **T004** — The implementer provided no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a Makefile/CI script invoking flake8/black). No evidence of the tools being set up or integrated into the project is present, so the requirement to configure flake8 and Black is not satisfied.
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/io.py
- **T005a** — declared artifact(s) missing/empty/invalid: src/utils/validation.py
- **T006** — declared artifact(s) missing/empty/invalid: src/config.py
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/edge_case_handler.py
