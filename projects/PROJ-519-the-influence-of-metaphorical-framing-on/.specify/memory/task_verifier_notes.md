# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required `src/` and `tests/` directories being present at the repository root is provided; the only material shown is a feature specification, not the filesystem structure. The implementer must add the two directories (with at least placeholder files) to satisfy the task.
- **T001b** — No evidence of a `data/` folder with the required subdirectories (`raw`, `processed`, `derived`) is provided; the claim lacks any artifact or file listing confirming the directory structure exists.
- **T001c** — No evidence of a `config/` directory being present was provided; the implementer did not supply any artifact showing that the required directory exists. The task remains undone until the `config/` folder is created and visible in the project.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present, nor any evidence that ruff/flake8 and black have been set up for the project. The provided artifacts relate only to the research feature, not to the required linting/formatting setup.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — No evidence of the required `data/raw`, `data/processed`, and `data/derived` directories or accompanying `.gitkeep` files is present; the implementer’s claim is not substantiated by any provided artifacts. The task remains undone until the directory structure with placeholder files is created in the repository.
- **T008** — No .env file, dotenv loading code, or documentation of environment variable usage is present; the implementer provided no tangible artifact demonstrating that configuration management for API keys and paths has been set up. The required setup is therefore missing.
- **T012** — declared artifact(s) missing/empty/invalid: src/data_ingestion.py
- **T013** — declared artifact(s) missing/empty/invalid: src/experiment_runner.py, data/raw/simulated_participants.csv, data/raw/survey_responses.json, data/processed/experimental_assignments.csv
- **T013b** — declared artifact(s) missing/empty/invalid: src/survey_interface.py, src/data_collection.py, data/processed/experimental_assignments.csv, data/raw/survey_responses.json
- **T014** — declared artifact(s) missing/empty/invalid: src/cami_scoring.py, data/raw/survey_responses.json, data/processed/cami_scores.csv
- **T014a** — declared artifact(s) missing/empty/invalid: src/data_ingestion.py, data/raw/survey_responses.json
