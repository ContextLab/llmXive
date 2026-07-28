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
- **T026** — The required file `src/analysis/forgetting_metrics.py` does not exist, so no evaluation logic was provided to compute the accuracy drop. The task’s core artifact is missing.
- **T030** — No code, script, or data file was presented that gathers the batch runner outputs from `data/results/` nor checks that at least 30 runs exist before analysis. The required aggregation logic and verification step are missing.
- **T035** — No `docs/` directory or `quickstart.md` file containing the required examples of running the three conditions was provided. The claim cannot be verified because the necessary documentation artifacts are missing.
