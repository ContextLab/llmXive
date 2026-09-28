# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or pre‑commit hook definitions) were provided, nor any evidence that ruff/flake8 and Black have been set up and run. The required artifacts are missing, so the task is not satisfied.
- **T004** — declared artifact(s) missing/empty/invalid: src/lib/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/lib/data_loader.py
- **T006** — The required file `src/lib/tool_mapper.py` does not exist, so the functionality to load the JSON, extract per‑problem `tool_descriptions`, and raise `ERR_TOOL_MAPPING_MISSING` cannot be verified. The missing artifact must be added and contain the described logic.
- **T014** — declared artifact(s) missing/empty/invalid: src/services/retrieval_service.py, src/lib/tool_mapper.py
- **T015** — declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- **T016** — declared artifact(s) missing/empty/invalid: src/cli/run_diagnostic.py, results/error_log.txt
- **T017** — No code, test, or log artifact was provided showing that records lacking a “thinking” prefix are now skipped and that the error `ERR_MISSING_THINKING` is logged. The implementer’s claim cannot be verified without such implementation evidence.
