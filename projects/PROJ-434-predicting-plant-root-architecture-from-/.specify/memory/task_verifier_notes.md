# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listings or screenshots were provided showing the required folders (`code/`, `data/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `artifacts/`, `figures/`). Without concrete evidence that these directories exist and are non‑empty, the claim cannot be verified. The implementer must supply a file‑system view (e.g., `tree` output or a zip archive) confirming the full structure.
- **T001c** — No `.gitignore` file was presented in the evidence; the implementer did not supply the required artifact, nor any content showing that a Python‑and‑data‑artifact ignore list was created. The task remains undone.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`, or CI scripts invoking ruff/flake8/black) are present in the provided artifacts, so the task of configuring these tools is not satisfied. The implementer must add the appropriate configuration files and ensure they are functional.
- **T004** — No evidence of a `code/utils/` directory or an `__init__.py` file was provided; the claim cannot be verified without those artifacts present. The required directory and initialization file are missing.
- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — No `.env` file, configuration script, or documentation for handling API keys is present in the provided evidence; the task required concrete environment configuration management artifacts, which are missing.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/merged_dataset.csv, data/processed/excluded_species_summary.csv, data/logs/species_exclusions.log
- **T024** — No `artifacts/model_metrics.json` file was presented; the response contains no JSON content, schema, or metric values. Consequently the required artifact is missing, so the task is not satisfied.
- **T025** — declared artifact(s) missing/empty/invalid: figures/feature_importance.png
- **T030** — No `quickstart.md` or `research.md` files were presented in the evidence, and there is no content indicating they were created or populated. The required documentation artifacts are missing, so the task is not satisfied.
- **T031** — No code files, refactored scripts, or documentation were provided in the `code/` directory, nor any evidence (e.g., diff, commit log, before‑after comparison) showing that cleanup or refactoring was performed. The claim lacks any tangible artifact to verify the required work.
