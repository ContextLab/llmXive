# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — No evidence of a `config.py` file in the specified directory is provided, nor any content showing the required constants (`RANDOM_SEED=42`, `MAX_RAM_GB=7`, `BATCH_SIZE = 64`). Consequently, the acceptance test `test_config.py` cannot have been run successfully. The implementer must add the file with the exact constants and ensure the test suite passes.
- **T014** — No evidence of a `utils.py` file in the specified directory was provided, nor any view of its contents showing a `validate_schema` function or passing `test_utils.py`. The required artifact is missing, so the task is not satisfied.
- **T016a** — declared artifact(s) missing/empty/invalid: data/processed/taxonomy_agentdog.json
- **T016b** — No evidence of a modified `taxonomy_builder.py` implementing `tracemalloc` monitoring or of a passing `test_memory.py` is provided. The required code changes, the memory‑limit enforcement logic, and the pytest results are missing, so the task’s acceptance criteria are not demonstrated.
- **T016c** — declared artifact(s) missing/empty/invalid: data/processed/taxonomy_centroids.json
