# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `tests/`, `data/`, `results/`, `specs/`) is provided; the response contains only the task description and no actual project‑structure artifacts. The implementer must create and show these folders (and ideally populate them) to satisfy the requirement.
- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml/black settings, or setup.cfg) were provided in the `code/` directory, nor any evidence that flake8 or black have been set up. The required artifacts are missing, so the task is not satisfied.
- **T004** — The provided `code/reference_validator.py` is truncated (ends at `fo`) and does not contain the logic that iterates over the extracted URLs, records failures, halts the pipeline, or writes specific errors to `data/logs/validation_error.log`. Consequently the required log file is also missing. The script must be completed and the log file generated for the task to be satisfied.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — The provided `code/data_ingestion.py` does not contain a `filter_valid_movies()` implementation (the file is truncated before any such function appears), and the required log file `data/logs/ingestion_log.txt` is absent. Consequently the filtering logic, logging, and error‑raising requirements are not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/processed/merged_clean.parquet, data/logs/ingestion_log.txt
