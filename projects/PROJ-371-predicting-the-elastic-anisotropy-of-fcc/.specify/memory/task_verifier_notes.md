# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The claim only states the intended command; no actual directory tree or file listing is provided to confirm that `src/data`, `src/models`, `src/utils`, `src/cli`, `tests/unit`, `tests/integration`, `data/raw`, `data/processed`, and `output` were created. Without concrete evidence of these folders existing, the task requirement is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or related setup scripts are present in the provided evidence, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration artifacts.
- **T004** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T007** — No evidence of the required `data/raw/` and `data/processed/` directories or accompanying `.gitkeep` files is provided; the implementer’s claim cannot be verified against any actual artifacts. The task remains undone until those directories with non‑empty `.gitkeep` placeholders are present in the repository.
- **T011** — The integration test file `tests/integration/test_pipeline.py` is present, but the required static manifest `data/raw/manifest_subset.json` is missing, so the test cannot run on a known subset of FCC IDs as specified. The missing manifest must be added with a list of valid material IDs.
- **T012** — declared artifact(s) missing/empty/invalid: src/data/ingest.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/features.py
- **T017** — No artifacts (e.g., CI logs, script output CSV/JSON, performance metrics, or a report) were provided to demonstrate that the data pipeline was executed on a free‑tier CI runner with CPU‑only resources and a sample subset of entries. Without such evidence the claim cannot be verified.
