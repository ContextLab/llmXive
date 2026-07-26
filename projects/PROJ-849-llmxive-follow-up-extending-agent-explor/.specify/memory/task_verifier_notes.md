# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/` directory or any files within it was provided; the claim lacks the required project‑structure artifacts. The implementer must create the specified folder hierarchy and populate it with the initial codebase as outlined in the implementation plan.
- **T002** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T003** — The implementer provided only a feature specification for semantic divergence diagnostics and no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or Black settings). There is no evidence that ruff and black have been installed, configured, or integrated into the project, so the task requirement is unmet.
- **T004** — declared artifact(s) missing/empty/invalid: src/lib/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/lib/data_loader.py
- **T006** — declared artifact(s) missing/empty/invalid: src/lib/tool_loader.py, data/tool_mappings/mathvista_tool_map.json
- **T006b** — declared artifact(s) missing/empty/invalid: src/cli/run_diagnostic.py
- **T007** — declared artifact(s) missing/empty/invalid: src/lib/axpo_simulator.py
- **T008** — No evidence of the required `tests/unit/` and `tests/contract/` directories being created is present; the submission contains only the task description and specifications, with no filesystem artifacts or file listings showing those directories. The implementer must add the two test directories (and optionally placeholder test files) to satisfy the task.
- **T017** — declared artifact(s) missing/empty/invalid: src/cli/run_diagnostic.py
- **T018** — No code, configuration, or documentation implementing the required memory‑monitoring logic was provided. The claim lacks any artifact (e.g., a Python module, script, or test) that checks RAM usage, enforces the ≤ 7 GB limit, or performs automatic down‑sampling when the limit is exceeded, so the task is not satisfied.
- **T011** — The required source file `src/models/divergence_model.py` is missing entirely, so there is no output schema to test. The existing `tests/contract/test_schemas.py` only defines a dataclass and validation logic (and is truncated), but does not contain actual pytest contract tests for the divergence model’s output. To complete the task, implement `divergence_model.py` with the expected output structure and add a proper contract test in `tests/contract/test_schemas.py` that validates that structure.
- **T012** — The required file `tests/unit/test_retrieval.py` does not exist, so no unit test for the BM25 zero‑results edge case is present. The implementer must add the missing test file with appropriate test code.
- **T014** — declared artifact(s) missing/empty/invalid: src/services/retrieval_service.py
- **T015** — declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- **T016** — declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- **T017#1** — declared artifact(s) missing/empty/invalid: src/models/divergence_model.py
- **T021** — declared artifact(s) missing/empty/invalid: src/lib/axpo_simulator.py
- **T022** — declared artifact(s) missing/empty/invalid: src/services/analysis_service.py
