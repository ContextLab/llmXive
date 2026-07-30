# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/` directory or any files within it was provided; the claim lacks the required project‑structure artifacts. The implementer must create the specified folder hierarchy and populate it with the initial codebase as outlined in the implementation plan.
- **T003** — The implementer provided only a feature specification for semantic divergence diagnostics and no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or Black settings). There is no evidence that ruff and black have been installed, configured, or integrated into the project, so the task requirement is unmet.
- **T004** — declared artifact(s) missing/empty/invalid: src/lib/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/lib/data_loader.py
- **T006** — The required file `src/lib/tool_mapper.py` does not exist, so the functionality to load the JSON, extract per‑problem `tool_descriptions`, and raise `ERR_TOOL_MAPPING_MISSING` cannot be verified. The missing artifact must be added and contain the described logic.
- **T007** — declared artifact(s) missing/empty/invalid: src/lib/metrics.py
- **T008** — No evidence of the required `tests/unit/` and `tests/contract/` directories being created is present; the submission contains only the task description and specifications, with no filesystem artifacts or file listings showing those directories. The implementer must add the two test directories (and optionally placeholder test files) to satisfy the task.
- **T014** — declared artifact(s) missing/empty/invalid: src/services/retrieval_service.py, src/lib/tool_mapper.py
- **T015** — declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- **T016** — declared artifact(s) missing/empty/invalid: src/lib/data_loader.py, src/cli/run_diagnostic.py
- **T016#1** — declared artifact(s) missing/empty/invalid: src/cli/run_diagnostic.py
- **T018** — No code, configuration, or documentation implementing the required memory‑monitoring logic was provided. The claim lacks any artifact (e.g., a Python module, script, or test) that checks RAM usage, enforces the ≤ 7 GB limit, or performs automatic down‑sampling when the limit is exceeded, so the task is not satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: src/lib/simulation_runner.py, results/cached_simulations.json
- **T023** — declared artifact(s) missing/empty/invalid: src/services/analysis_service.py
- **T024** — No code, test, or documentation was provided showing that a sample‑size check (N ≥ 30) was added to the correlation routine, nor that the system raises a “Statistical Power Insufficient” error when N < 30. The required artifact (implementation and/or test confirming this behavior) is missing.
- **T025** — No code, script, test, or documentation was provided that adds the required logic to detect and flag a “Significant Negative Correlation” when p < 0.05 and the correlation coefficient is negative. The claim lacks any concrete artifact (e.g., a function, module, or output file) demonstrating the implementation, so the task is not satisfied.
