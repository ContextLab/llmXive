# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/`, `data/`, or `tests/` directories (or any files within them) is provided; without these artifacts the claim that the project structure was created cannot be verified.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.flake8`, `ruff.toml`, or Black settings) or related scripts are present in the provided evidence, so the task of configuring ruff/flake8 and Black has not been demonstrated. The required artifacts are missing.
- **T004** — No evidence of a `code/utils/` directory or an `__init__.py` file within it was provided; the required artifacts are missing. The implementer must add the directory and a non‑empty `__init__.py` file.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — No `.env` file, configuration script, or documentation for handling API keys is present in the provided artifacts. The task required setting up environment configuration management, which is not demonstrated. The implementer must add a proper `.env` example (or template), code to load it (e.g., using python‑dotenv), and instructions for using it.
- **T016** — No code, configuration, or log files were provided that demonstrate logging of excluded records (e.g., missing soil data, failed geocoding, low‑sample species). Without an actual implementation or example log output, the requirement to add and record these exclusions is not satisfied. The next implementer must add the logging logic to the ingestion pipeline and supply the resulting log excerpts or code showing the log statements.
- **T025** — No `artifacts/model_metrics.json` file was presented; the response contains no JSON content, schema, or metric values. Consequently the required artifact is missing, so the task is not satisfied.
- **T026** — declared artifact(s) missing/empty/invalid: figures/feature_importance.png
