# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (code/, data/raw, data/processed, tests/) is provided; the implementer did not supply any artifact showing that the project structure was created.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) were provided or referenced, so the required artifact for configuring ruff/flake8 and Black does not exist. The task therefore remains unfinished.
- **T005** — The provided `code/synthetic_generator.py` is truncated (metadata dict incomplete, no CSV write, no return of required fields) and the required output file `data/processed/synthetic_mar_v1.csv` does not exist. Additionally, the referenced schema file `contracts/dataset.schema.yaml` is missing, so the generated dataset cannot be validated against it.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
