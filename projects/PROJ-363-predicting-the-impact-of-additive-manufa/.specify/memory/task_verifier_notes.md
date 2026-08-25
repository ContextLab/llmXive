# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required `code/`, `tests/`, `data/`, `results/`, or `models/` directories is provided; the response contains only textual specifications and no filesystem artifacts. The implementer must create these directories in the repository root.
- **T001b** — No directory `projects/PROJ-363-predicting-the-impact-of-additive-manufa/` is shown in the provided artifacts, nor any listing confirming its creation; thus the required subdirectory structure is missing.
- **T003** — The submission provides no linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or scripts to set them up, so the required artifact for task T003 is missing.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — No `code/` directory, `__init__.py`, or placeholder files for data, models, and results are present in the provided evidence; the claim cannot be verified without those artifacts.
- **T007** — declared artifact(s) missing/empty/invalid: state.yaml
- **T008** — No `.env` example file or `utils.py` containing environment‑loading logic was provided; the evidence contains only the task description and user stories, with no actual code or files to verify that the configuration management was implemented. The required artifacts are missing.
- **T013** — The repository contains `code/download_data.py`, but the file is truncated and does not show any SHA‑256 checksum computation or writing of results to a `state.yaml`. Moreover, the required `state.yaml` file is missing entirely, so the script cannot update it as specified. The implementer must add the checksum logic and create/update `state.yaml` after a successful download.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_316L.csv, state.yaml
- **T026** — declared artifact(s) missing/empty/invalid: results/reports/model_metrics.json
- **T027b** — declared artifact(s) missing/empty/invalid: results/reports/model_metrics.json
