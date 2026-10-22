# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-011 (Data source must be polymer degradation records from NIST Chemistry WebBook and Materials Project; no other datasets) is not referenced by any task in the implementation plan. The plan only mentions the WebBook CSV and does not address the Materials Project source, leaving this functional requirement unbacked.
- FR-012 (Repository shall contain the directories `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/`, `state/`, `state/projects/`) is not linked to any task in the plan. No phase/task explicitly creates or verifies this directory structure.
- FR-013 (A `state/setup_log.txt` file shall be generated containing a recursive directory listing with a timestamp) is absent from the plan. No task creates or logs this file, so the requirement is unaddressed.
- FR-014 (The codebase shall include a `code/.ruff.toml` with strict linting and a CI step that runs `ruff check code/` with exit code 0) is not covered. The plan lists lint‑checking tasks (T003a,b) but does not tie them to FR‑014 or provide evidence of the required CI step.
- FR-015 (Test configuration shall include a `pytest.ini` with deterministic seed pinning and a `tests/conftest.py` file) is not linked to any plan task. The plan mentions pytest setup (T008a‑c) but does not reference the required `conftest.py` or seed‑pinning configuration.
- The `model_output.schema.yaml` contract is listed but no implementation step in the plan generates or validates artifacts conforming to this schema (e.g., no task produces a `ModelOutput` JSON file).
