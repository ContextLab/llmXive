# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`data/raw`, `data/processed`, `code`, `tests`, `docs`) was shown or listed in the provided evidence, so we cannot confirm that the required project folders exist and contain any content. The implementer must supply a view of the repository showing these directories (and preferably non‑empty placeholder files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8` files) or scripts/CI steps are present in the provided evidence, so the requirement to configure ruff/flake8 and Black has not been demonstrated. The implementer must add the appropriate configuration files and show they are active (e.g., a sample run output).
- **T004** — No GitHub Actions workflow file (e.g., `.github/workflows/ci.yml`) was provided or referenced, and there is no evidence that a CI pipeline installing R‑base, the R packages `lme4` and `ordinal`, and the required Python dependencies exists. The task therefore remains unfulfilled.
- **T005** — No `.gitignore` file was presented, and there is no evidence of its contents containing the required patterns (`data/raw/*` except `.gitkeep`, `data/processed/*`, `__pycache__`, model caches). The task’s deliverable is therefore missing.
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No `.env` template file containing an `HF_TOKEN` placeholder was provided or referenced; the claim contains only the higher‑level feature specification, not the required environment‑configuration artifact. The task remains undone until a proper `.env` template is added.
- **T011** — The `code/utils/schema_validator.py` file exists, but the required schema `contracts/dataset.schema.yaml` is missing, so the validator cannot actually validate against the intended contract. Additionally, the shown source is truncated, suggesting the implementation may be incomplete. The missing schema file must be added (or the path corrected) and the validator fully implemented to meet the task.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/scored_dialogues.parquet, data/raw/exclusions.log
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/clmm_results.csv
