# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T001c** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8` files, or a setup script invoking ruff/flake8) were presented, nor any evidence that such tools have been run. The required artifacts to demonstrate that linting and formatting are configured are missing.
- **T003** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004** — No Python code or configuration file implementing a `logging` setup with file handlers is present, nor any evidence (e.g., log output, screenshots, tests) showing that warnings for indeterminate trajectories are captured. The required artifact – a concrete logging infrastructure implementation – is missing.
- **T005** — No configuration file, script, or code implementing URL and checksum verification for the HuggingFace `materials-science/amorphous-silicon-shear-trajectories` dataset is present. The required environment setup and validation logic are missing, so the task is not satisfied.
- **T006** — The `code/data_generator.py` file is truncated and contains a stray `yield` statement, so it does not actually generate the HDF5 files, assign brittle/ductile labels, or write a `metadata.json`. Moreover, the required `data/raw/metadata.json` file is missing entirely. The task’s output artifacts are therefore absent or non‑functional.
