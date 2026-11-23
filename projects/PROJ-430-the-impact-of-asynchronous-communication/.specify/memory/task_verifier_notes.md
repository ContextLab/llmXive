# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project root contains `code/`, `data/`, and `tests/` but the required `docs/` and `config/` sub‑directories are absent, and the provided test script fails because it looks for `projects/code/init_project_structure.py` instead of the correct path. The directory structure does not fully meet the task specification.
- **T001c** — The evidence shows the `data/raw/` and `data/derived/` directories but no `.gitignore` file at `projects/PROJ-430-the-impact-of-asynchronous-communication/.gitignore`, nor any content confirming the required exclusion patterns. The required artifact is missing.
- **T002b** — Requested task execution failed; rerun successfully: code/install_dependencies.py exit=1
- **T003** — The `.ruff.toml` and `pyproject.toml` files exist and contain reasonable configurations, but there is no provided evidence (e.g., command output, log file, CI step) that an initial lint/formatting check was actually executed. The task’s requirement to “run initial lint check” is therefore unmet.
- **T004** — The `code/config.py` file is present and defines paths and the deferred thresholds (`sample_size`, `min_events`, `deferred_threshold`), but it does not provide any mechanism for configuring or loading API keys as required by the task. Adding support for API key storage (e.g., reading from environment variables or a `config.json` entry) is needed to satisfy the specification.
- **T010a** — declared artifact(s) missing/empty/invalid: code/ingestion.py
- **T015** — Requested task execution failed; rerun successfully: code/aggregate_project_metrics.py exit=1
- **T022a** — declared artifact(s) missing/empty/invalid: data/validation/sampling_request.json
- **T023b** — declared artifact(s) missing/empty/invalid: data/validation/validation_report.json
- **T024** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_rate.json
- **T029** — declared artifact(s) missing/empty/invalid: data/derived/corrected_pvalues.json
