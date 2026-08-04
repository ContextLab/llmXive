# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/`, `data/`, and `tests/` directories was provided; the artifact list is empty, so the project structure has not been demonstrated. The implementer must create and show these three top‑level folders (with at least placeholder files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `black` config) or setup scripts are present in the provided evidence, so the requirement to configure ruff and black is not demonstrated. The implementer must add the appropriate configuration files and ensure they are applied to the codebase.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — No evidence of the required `data/raw/`, `data/processed/`, or `data/graphs/` directories or their `.gitkeep` placeholder files is provided; without these artifacts the task is not satisfied.
- **T007** — No configuration loader code or related files were presented; the claim provides no artifact implementing environment‑variable handling or dataset‑path configuration, so the required base config loader is missing.
- **T010** — declared artifact(s) missing/empty/invalid: scripts/ingest.py
- **T016** — No code, CSV, or configuration changes were provided that show tasks are flagged as “Unparseable,” retained in the ground‑truth CSV with a status field, or that T015, T019, and T020 skip the tree‑sitter step for those rows. The required implementation artifacts are missing.
- **T019** — declared artifact(s) missing/empty/invalid: scripts/extract_features.py
- **T022** — No code, script, or documentation implementing the fallback logic for “semantic_complexity” is provided; the artifact is missing entirely, so the requirement cannot be verified as satisfied.
