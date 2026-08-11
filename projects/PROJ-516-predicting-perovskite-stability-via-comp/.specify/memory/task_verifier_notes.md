# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-516-predicting-perovskite-stability-via-comp/` directory or any files inside it is provided; the claim lacks the required project‑structure artifacts. The implementer must create the folder and populate it with the expected sub‑directories and starter files (e.g., `data/`, `src/`, `scripts/`, `README.md`, etc.) as outlined in the implementation plan.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pylintrc`, `pyproject.toml` with Black/isort settings, or associated setup scripts) were presented, nor any evidence that these tools have been integrated into the project’s CI pipeline. Without such artifacts, the requirement to configure flake8/pylint and Black/isort is not satisfied.
- **T004** — No `state_manager.py` file or any code that computes SHA‑256 hashes and updates the `state/...yaml` files is present in the provided evidence. The claim lacks the required artifact, so the task is not satisfied.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No `.env` file or any configuration snippet was presented, and there is no evidence that API keys for Materials Project and NREL have been stored securely in an environment file. The required artifact is missing, so the task is not satisfied.
- **T012** — The required output file `data/raw/nrel_perovskites.csv` is absent, and the provided `code/data_ingestion.py` is truncated (ends mid‑function) with no visible logic that actually writes the filtered DataFrame to that path. Consequently the task’s core requirement—fetching, validating, filtering for `T_d` entries, and persisting them to the specified CSV—has not been demonstrably fulfilled.
- **T013a** — declared artifact(s) missing/empty/invalid: data/raw/metadata.json
- **T013b** — declared artifact(s) missing/empty/invalid: data/raw/metadata.json, schema.yaml
- **T013c** — declared artifact(s) missing/empty/invalid: data/raw/uncertainty_flags.json
- **T014** — The repository contains a `code/feature_engineering.py` file, but its content is truncated and does not show the full logic for computing the required descriptors or writing them to a CSV. Moreover, the expected output file `data/processed/descriptors.csv` is absent. Both the generation of the descriptor matrix and the creation of the CSV output are missing, so the task is not fulfilled.
- **T014b** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
