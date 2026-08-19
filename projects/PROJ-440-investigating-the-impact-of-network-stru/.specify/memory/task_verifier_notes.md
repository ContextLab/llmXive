# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or other evidence was provided showing that the required folders (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`) actually exist; without such artifacts the claim cannot be confirmed.
- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.flake8` config, or related CI scripts) are present in the provided evidence, so the required artifact for configuring ruff/flake8 and black does not exist. The implementer must add the appropriate configuration files and ensure they are functional.
- **T003** — No pre‑commit configuration files (e.g., `.pre-commit-config.yaml`, hook scripts, or documentation of hook installation) are present in the provided artifacts, so the requirement to configure linting/formatting hooks is not satisfied. The claim lacks any concrete evidence of the requested setup.
- **T006a** — The required file `contracts/network_schema.schema.yaml` is absent from the repository, so no schema definition is provided despite the presence of `data/raw/networks.csv`. The task explicitly demands this schema file, which is missing.
- **T006b** — declared artifact(s) missing/empty/invalid: data/processed/energy_decay.csv, schema.yaml
- **T006c** — declared artifact(s) missing/empty/invalid: data/analysis/regression_results.json, schema.yaml
- **T008** — No `data/` directory with the required `raw/`, `processed/`, and `analysis/` subfolders was provided, nor any checksumming utility scripts or files. The implementer’s claim lacks any tangible artifact to verify that the directory structure and utilities were actually created.
- **T016** — No code, test, or documentation showing that error handling for generation failures was added, that specific graph IDs are logged, or that failed graphs are excluded from the final dataset is present. The required artifact (updated generation script with logging and exclusion logic) is missing.
