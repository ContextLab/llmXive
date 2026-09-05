# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree, no `__init__.py` files, and no evidence of the `mkdir -p …` command execution were provided. The required project structure and empty init files are missing, so the task is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, pre‑commit hooks, or documentation) are present in the provided evidence, so the requirement to configure Ruff and Black is not satisfied. The implementer must add the appropriate configuration artifacts and verify they are functional.
- **T004** — declared artifact(s) missing/empty/invalid: src/config.py
- **T007** — declared artifact(s) missing/empty/invalid: src/data/loaders.py
- **T008** — declared artifact(s) missing/empty/invalid: src/pipeline/logging_config.py
- **T014b** — No code, script, or function implementing the required `ExtremeEvent` entity mapping logic was provided. The task demands a concrete implementation that takes raw NOAA GHCN‑Daily records and outputs records with fields (station_id, date, magnitude, threshold_value); such an artifact is absent, so the requirement is not satisfied.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/extreme_events.parquet
- **T016** — declared artifact(s) missing/empty/invalid: src/data/summary.py
- **T021** — declared artifact(s) missing/empty/invalid: src/pipeline/run_analysis.py
- **T020b** — declared artifact(s) missing/empty/invalid: src/pipeline/run_analysis.py
- **T019** — declared artifact(s) missing/empty/invalid: src/models/gpd_baseline.py
