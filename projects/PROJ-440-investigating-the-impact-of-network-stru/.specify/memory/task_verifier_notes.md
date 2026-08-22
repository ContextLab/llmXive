# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or any file system evidence was provided showing that the required folders (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`) actually exist; the claim is unsubstantiated.
- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml` entries, `.ruff.toml`, `.flake8`, or `black` settings) were provided, nor any documentation showing that ruff/flake8 and black have been set up for the project. Consequently, the required artifact to satisfy task T002 is missing.
- **T003** — No pre‑commit configuration files (e.g., `.pre-commit-config.yaml`), hook scripts, or documentation of linting/formatting tools are present. The required artifact to show that pre‑commit hooks have been set up and are functional is missing.
- **T006a** — The required file `contracts/network_schema.schema.yaml` does not exist, so the schema defining the structure of `data/raw/networks.csv` was never created. The CSV file is present, but the essential schema artifact is missing.
- **T006b** — The required schema file `contracts/energy_schema.schema.yaml` does not exist in the repository, so the task of defining the data structure for `data/processed/energy_decay.csv` is not fulfilled. The CSV file is present, but the mandatory schema artifact is missing.
- **T006c** — The required file `contracts/regression_schema.schema.yaml` is missing from the repository, so no schema defining the structure of `data/analysis/regression_results.json` is present. Without this artifact, the task is not fulfilled.
