# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked the actual repository tree under `projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/` against the directory layout described in the “Project Structure” section of `plan.md`. The observed layout contains extra top‑level entries (e.g., `.runtime-home/`, `.specify/`, `config/`, `docs/`, `figures/`, `idea/`, `pyproject.toml`, a root‑level `requirements.txt`) and places the `tests/` directory at the repository root instead of under `code/tests/` as required. Consequently the on‑disk structure does not faithfully match the specified tree.
- **T003** — I inspected the project root (`projects/PROJ-811-llmxive-follow-up-extending-many-shot-co`) for any linting/formatting configuration artifacts (e.g., `ruff.toml`, `.ruff.toml`, `pyproject.toml` sections for Black, a `pre-commit` hook, or scripts invoking `ruff`/`black`). No such files or configuration entries were present in the collected evidence, so the requirement to configure linting with Ruff and formatting with Black is not satisfied. Adding the appropriate configuration files and/or scripts is needed.
- **T004** — The `data/` directory is present, but its `results/` subdirectory is missing, and there is no evidence that an `artifacts/` directory (for checksums) was created. Both are required to satisfy task T004.
- **T006** — The evidence only shows the project root path; no configuration files (e.g., `.env`, `config.yaml`) or Python modules/functions that load seeds and model paths are present. Consequently, the required environment‑configuration management code is missing.
- **T048** — declared artifact(s) missing/empty/invalid: code/src/validate_splits.py
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/gold_standard_annotations.json
- **T015b** — declared artifact(s) missing/empty/invalid: data/processed/gold_standard_annotations.json
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/gold_standard_validation_report.json
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/dag_manifest.json
- **T024a** — Requested task execution failed; rerun successfully: code/src/run_generate_embeddings.py exit=1
- **T043** — declared artifact(s) missing/empty/invalid: code/tests/unit/
