# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — declared artifact(s) missing/empty/invalid: code/utils/setup_project.py
- **T003** — The evidence only shows the project root path; no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or associated scripts) are present or referenced. Without these artifacts, the task “Configure linting (ruff) and formatting (black)” is not satisfied. Adding the required configuration files and confirming they are non‑empty would be needed.
- **T048.0a** — Requested task execution failed; rerun successfully: code/research/ads_search.py exit=1
- **T004** — Checked the provided `config.yaml` (which exists) but no `config.py` artifact was found or shown, and thus there is no evidence that a Python module loads the YAML, extracts `benchmark_values.etvos_limit`, logs the required warning when missing, and sets the config attribute accordingly. The core implementation required by T004 is absent.
- **T006** — declared artifact(s) missing/empty/invalid: contracts/orbit_solution.schema.yaml
- **T007** — The schema file exists, but the `eta_value` field allows negative numbers (`minimum: -1.0`), violating the task’s requirement that it be non‑negative. Adjust the schema to enforce `minimum: 0.0` (or otherwise ensure η ≥ 0).
- **T008** — The provided `code/utils/logging.py` correctly implements console and optional file handlers and defines the required `DataUnavailableError` and `ModelError` exceptions. However, there is no evidence that the module is imported by the tasks T009, T016, and T018; no import statements or usage traces are shown for those modules. This requirement is unmet.
- **T009b** — declared artifact(s) missing/empty/invalid: data/satellite_metadata.yaml
- **T014b** — declared artifact(s) missing/empty/invalid: code/ingestion.py
- **T014c** — declared artifact(s) missing/empty/invalid: code/ingestion.py
- **T017** — declared artifact(s) missing/empty/invalid: code/preprocessing.py
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/excluded_satellites.json
- **T019** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T009** — declared artifact(s) missing/empty/invalid: code/ingestion/downloader.py, data/feasibility_gap_report.json
- **T023c** — declared artifact(s) missing/empty/invalid: code/dynamics/models.py
- **T023d** — declared artifact(s) missing/empty/invalid: code/dynamics/models.py
- **T023e** — declared artifact(s) missing/empty/invalid: code/dynamics/models.py
- **T023f** — declared artifact(s) missing/empty/invalid: code/dynamics/force_calculator.py
- **T028** — declared artifact(s) missing/empty/invalid: data/results/orbit_solutions.json, data/results/eotvos_metrics.json
- **T036** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_analysis.png
- **T049** — declared artifact(s) missing/empty/invalid: code/analysis/report.py
- **T049b** — declared artifact(s) missing/empty/invalid: code/analysis/report.py
