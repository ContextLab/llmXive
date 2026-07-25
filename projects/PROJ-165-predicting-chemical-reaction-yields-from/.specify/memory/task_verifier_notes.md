# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required project directories (`src/`, `data/`, `tests/`, `state/`) is provided; the claim lacks any artifact showing that these folders exist or contain files. The implementer must add the directory structure (and preferably placeholder files) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.flake8`, or related CI scripts) were presented, nor any evidence that these tools have been set up and run. The required artifacts are missing, so the task is not satisfied.
- **T004** — declared artifact(s) missing/empty/invalid: src/utils/seeds.py
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/validators.py
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: src/cli/main.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/ingestion.py, data/validation_status.json, data/ingestion_log.json
- **T017a** — The provided `src/data/preprocessing.py` contains only spectral resampling logic and does not implement the required reaction‑template‑based splitting, overlap checking, or condition‑feature integration. Moreover, the required output artifacts `data/processed/split_indices.parquet` and `data/artifacts/split_manifest.json` are absent. The task’s core deliverables are therefore missing.
- **T018** — declared artifact(s) missing/empty/invalid: src/data/loaders.py
- **T019** — No evidence of a `data/` directory with the required `raw/`, `processed/`, and `artifacts/` subfolders is shown, nor any code or log demonstrating checksum logging in a `state/` location. The implementer’s claim lacks the necessary artifacts to verify that the directory structure was created and that checksum logging was implemented.
- **T020** — declared artifact(s) missing/empty/invalid: data/artifacts/leakage_report.json
- **T023** — declared artifact(s) missing/empty/invalid: src/models/baselines.py
- **T024** — declared artifact(s) missing/empty/invalid: src/models/attention_net.py
