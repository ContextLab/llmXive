# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/requirements.txt
- **T006** — No linting/formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` and `[tool.ruff]`, a `.ruff.toml`, or a `pre-commit` config) were provided for the `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/` directory, nor any evidence that `ruff` and `black` have been installed or run. The required artifacts are missing, so the task is not satisfied.
- **T011** — declared artifact(s) missing/empty/invalid: projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/contracts/output_schema.yaml
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/static_scores.json
- **T018** — No code, configuration, or log files were presented that implement the required timing‑monitoring, exclusion logging (“TIMEOUT_EXCLUDED”), or the exit‑on‑high‑exclusion‑rate behavior (“RESOURCE_LIMIT_EXCEEDED”). The artifact needed to demonstrate this logic is missing.
- **T025** — No code, data file, or documentation was provided that implements the required failure‑handling logic (recording a negative likelihood gain or a failure state when the policy cannot find a solution). Without any artifact to inspect, we cannot confirm the feature was added. The task remains unimplemented.
- **T026** — The required unit test file `tests/unit/test_alignment.py` is missing from the repository, so no test code exists to verify the alignment logic. Without this artifact, the task’s requirement is not satisfied.
- **T028** — The required integration test file `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_correlation_pipeline.py` is missing, so no test code exists to satisfy the task’s specification.
- **T029b** — The required output file `data/processed/dtw_alignment_matrix.json` is missing, and the `compute_dtw_alignment` function in `code/analysis/correlation.py` is truncated and not fully implemented. The task’s deliverables are therefore not present.
