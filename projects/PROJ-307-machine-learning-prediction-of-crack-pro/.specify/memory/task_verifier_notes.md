# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No evidence of any `__init__.py` files or placeholder module files in the `code/` directory is provided; the implementer did not supply the required artifacts, so the task is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — The provided `code/data/loader.py` exists and contains a `validate_schema` function, but the required schema file `contracts/dataset.schema.yaml` is missing, so the loader cannot actually consume the intended schema. Add the missing schema file (and optionally import any missing types) to satisfy the task.
- **T010** — No configuration or logging files (e.g., `config.yaml`, `.env`, `logging.py`, or similar) are present in the `code/` directory, nor is any evidence (code snippets, screenshots, test output) provided to demonstrate that environment configuration management and logging infrastructure have been set up. The required artifacts are missing, so the task is not satisfied.
- **T018** — No code, script, test, or documentation showing the added validation logic is provided; the claim lacks any concrete artifact demonstrating that the pipeline now halts when required columns are missing after cleaning. The required implementation is therefore not evidenced.
- **T025** — No code files or scripts were presented in `code/analysis/` that perform feature‑importance aggregation or extract the top‑3 features, and thus the required artifact is missing. The implementer must add the appropriate implementation (e.g., a Python module that reads model importance outputs, aggregates them across folds or models, and returns the three most important non‑ΔK features).
