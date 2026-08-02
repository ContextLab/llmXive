# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The implementer provided only a feature specification for semantic divergence diagnostics and no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or Black settings). There is no evidence that ruff and black have been installed, configured, or integrated into the project, so the task requirement is unmet.
- **T004** — declared artifact(s) missing/empty/invalid: src/lib/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/lib/data_loader.py
- **T006** — The required file `src/lib/tool_mapper.py` does not exist, so the functionality to load the JSON, extract per‑problem `tool_descriptions`, and raise `ERR_TOOL_MAPPING_MISSING` cannot be verified. The missing artifact must be added and contain the described logic.
- **T014** — declared artifact(s) missing/empty/invalid: src/services/retrieval_service.py, src/lib/tool_mapper.py
- **T015** — declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- **T016** — declared artifact(s) missing/empty/invalid: src/cli/run_diagnostic.py
- **T017** — No code, test, or log artifact was provided showing that records lacking a “thinking” prefix are now skipped and that the error `ERR_MISSING_THINKING` is logged. The implementer’s claim cannot be verified without such implementation evidence.
- **T018** — No code, configuration, or documentation implementing the required memory‑monitoring logic was provided. The claim lacks any artifact (e.g., a Python module, script, or test) that checks RAM usage, enforces the ≤ 7 GB limit, or performs automatic down‑sampling when the limit is exceeded, so the task is not satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: src/lib/simulation_runner.py, data/cached_axpo_results.json
- **T023** — declared artifact(s) missing/empty/invalid: src/services/analysis_service.py
