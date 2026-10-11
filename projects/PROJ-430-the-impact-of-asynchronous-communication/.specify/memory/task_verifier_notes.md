# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project root contains `code/`, `data/`, and `tests/` as required, but the `docs/` and `config/` directories specified in the task are absent. These missing directories prevent the task’s full directory‑structure requirement from being satisfied.
- **T001c** — The evidence shows the `data/raw/` and `data/derived/` directories but provides no `.gitignore` file at `projects/PROJ-430-the-impact-of-asynchronous-communication/.gitignore`, nor any content confirming the required exclusion patterns. The required artifact is missing.
- **T001d** — The `requirements.txt` file exists and lists all requested packages, but it does not pin them to specific versions (e.g., `pandas==1.5.0`). The task explicitly required “Pin dependencies,” so the artifact fails to meet the specification.
- **T002a** — The evidence provides only the project root path and no `venv/` directory or any output confirming that `venv/bin/python --version` returns Python 3.11.x. The required virtual‑environment artifact and its verification output are missing.
- **T002b** — Checked the presence of `requirements.txt`, which exists and lists packages, but there is no evidence that `pip install -r requirements.txt` was actually executed in a virtual environment nor any captured output showing the installed packages. The required execution log/output is missing.
- **T003** — The `.ruff.toml` and `pyproject.toml` files exist and contain reasonable configurations, but there is no provided evidence (e.g., command output, log file, CI step) that an initial lint/formatting check was actually executed. The task’s requirement to “run initial lint check” is therefore unmet.
- **T010a** — declared artifact(s) missing/empty/invalid: code/ingestion.py
- **T015** — Requested task execution failed; rerun successfully: code/aggregate_project_metrics.py exit=1
- **T022a** — declared artifact(s) missing/empty/invalid: data/validation/sampling_request.json
- **T023b** — declared artifact(s) missing/empty/invalid: data/validation/validation_report.json
- **T024** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_rate.json
- **T029** — declared artifact(s) missing/empty/invalid: data/derived/corrected_pvalues.json
