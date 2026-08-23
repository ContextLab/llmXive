# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No files or code were presented in `tests/contract/` that define JSON schema validators for the `dataset`, `agent_state`, and `result` structures, nor any evidence that they were derived from the contracts in `contracts/`. The required validator artifacts are missing, so the task is not satisfied.
- **T011** — declared artifact(s) missing/empty/invalid: src/generators/logic_generator.py
- **T012** — declared artifact(s) missing/empty/invalid: src/generators/grid_generator.py
- **T013** — declared artifact(s) missing/empty/invalid: src/generators/test_generator.py, data/test_instances.json
- **T014** — declared artifact(s) missing/empty/invalid: data/checksums.json
- **T015** — declared artifact(s) missing/empty/invalid: src/analysis/validate_dataset.py
- **T017** — The required file `tests/unit/test_agent_conditions.py` does not exist, so no unit test for the bidirectional exchange logic is present. The task’s artifact is missing entirely.
- **T018** — declared artifact(s) missing/empty/invalid: src/agents/sequential_agent.py
- **T019** — declared artifact(s) missing/empty/invalid: src/agents/mixed_agent.py
- **T020** — declared artifact(s) missing/empty/invalid: src/agents/coevolving_agent.py
- **T036** — No code files, refactored modules, or documentation were provided; consequently there is no evidence that type hints or docstrings have been added or completed. The required artifacts for the cleanup task are missing.
- **T037** — The implementer provided no code, configuration changes, profiling data, or benchmark results demonstrating that runs now finish within the CI time limit on limited CPU cores. No performance‑optimization artifact (e.g., optimized training loop, parallelism settings, CI timeout adjustments, or timing reports) is present, so the requirement is unmet.
