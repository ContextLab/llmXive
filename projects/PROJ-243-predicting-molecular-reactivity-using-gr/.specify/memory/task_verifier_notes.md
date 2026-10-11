# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The repository contains `requirements.txt`, `pyproject.toml`, and `ruff.toml`, and the install log shows the requirements install successfully, but there is no `.flake8` file present and the provided linting log does not include the output of `ruff check .` or `black --check .` confirming they pass without errors. Adding the missing `.flake8` file and supplying evidence that both ruff and black checks succeed is required.
- **T003** — The `data/raw/checksums_schema.yaml` file exists and appears valid, but the required `data/raw/checksums.json` is not empty—it contains entries with keys `file`, `hash`, and `path` that do not match the schema’s `file_path` and `sha256` fields. The task explicitly demanded an empty `checksums.json`, so this requirement is unmet.
