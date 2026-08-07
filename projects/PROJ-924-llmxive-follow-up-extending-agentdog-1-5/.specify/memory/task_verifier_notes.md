# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a pre‑commit hook) are present in the specified project directory, nor any evidence that ruff/black have been set up. The required artifacts are missing.
- **T011** — The claim provides no visible `config.py` file in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, nor any evidence that `test_config.py` runs and passes. Without the file containing the required constants (`RANDOM_SEED=42`, `MAX_RAM_GB=7`, `BATCH_SIZE=64`) and a passing test, the task is not satisfied. The implementer must add the file with the exact contents and ensure the pytest suite succeeds.
