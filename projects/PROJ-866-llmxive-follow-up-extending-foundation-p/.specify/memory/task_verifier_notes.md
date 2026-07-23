# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/`, `tests/`, `state/`) is provided; the response contains only a feature specification and no actual project structure artifacts.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml` entries) were provided, nor any evidence that Ruff and Black have been set up and integrated into the project. The required artifacts to demonstrate the configuration are missing.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — No evidence was provided that the three required directories (`data/raw/`, `data/processed/`, `data/results/`) actually exist in the repository; the response contains only the task description and no file‑system listing or screenshots confirming their creation. The implementer must add the directories (or show proof they are present) to satisfy the task.
- **T010** — The required file `tests/unit/test_generator.py` is missing from the repository, so no unit test for graph variance exists. Without this artifact, the task’s requirement is not satisfied.
- **T015** — No `main.py` file or any code skeleton is present in the provided evidence, and there is no indication that a script generating and saving raw workflows to `data/raw/` exists. The required orchestrator artifact is missing.
- **T016** — No code artifact (e.g., a modified `full_context.py` file) or execution‑log example was provided showing the new handling for single‑node graphs with `depth=0`, nor evidence that `context_reduction_pct` is set to the string `'[deferred]'` and `status` to `'edge_case'`. The required implementation and its verification are missing.
- **T032** — declared artifact(s) missing/empty/invalid: data/results/tradeoff_curve.csv
