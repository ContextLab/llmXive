# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/requirements.txt` file exists but lists only package names without version pins, violating the “pinned dependencies” requirement of the task. Version specifications (e.g., `pandas==1.5.3`) need to be added.
- **T003** — The evidence only shows the project root path; no linting or formatting configuration files (e.g., `.flake8`, `.pylintrc`, `pyproject.toml`/`setup.cfg` with black/isort settings) are present or referenced. Without these artifacts, the requirement to configure flake8, pylint, black, and isort is not satisfied. Adding the appropriate config files and confirming they are non‑empty will be needed.
- **T004** — The evidence provided does not show the existence of the required directories `data/raw`, `data/processed`, or `outputs` within the project root, nor any files confirming they were created. Without concrete proof that these folders were set up, the task requirement is not satisfied.
- **T006** — The `code/utils/` directory contains the expected files (`config.py`, `logger.py`, etc.), but no evidence of their contents is provided. Without seeing the actual implementation, we cannot confirm that a base configuration and a functional logging infrastructure were created as required. The implementer must supply the source code (or execution evidence) showing that these modules define configuration settings and a working logger.
- **T017** — Requested task execution failed; rerun successfully: code/drift_analysis.py exit=1
- **T025** — declared artifact(s) missing/empty/invalid: outputs/drift_metrics.csv
- **T026b** — declared artifact(s) missing/empty/invalid: outputs/global_stats.json
