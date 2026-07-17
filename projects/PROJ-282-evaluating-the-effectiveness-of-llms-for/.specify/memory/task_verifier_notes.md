# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `src/`, `tests/`, or `data/` directories is provided; the implementer’s claim is unsupported by any visible artifacts. The task cannot be considered fulfilled until those directories are created and contain appropriate project files.
- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` and `[tool.ruff]`, `.ruff.toml`, or a `.pre-commit-config.yaml` invoking ruff and black) were provided or referenced, so we cannot verify that the tools are actually set up. The required artifacts are missing.
- **T004** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logger.py
- **T007** — declared artifact(s) missing/empty/invalid: src/models/code_snippet.py
- **T008** — declared artifact(s) missing/empty/invalid: src/models/feature_vector.py
- **T009** — declared artifact(s) missing/empty/invalid: src/models/prediction_result.py
- **T010** — declared artifact(s) missing/empty/invalid: src/utils/hash_artifacts.py
- **T011** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T012** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T013** — declared artifact(s) missing/empty/invalid: src/models/llm_inference.py
- **T014** — No `llm_inference.py` file or diff showing the required truncation‑event logging and ambiguous‑response regex mapping was provided; without the actual code changes we cannot confirm the logic was added. The implementer must supply the updated `llm_inference.py` (or a patch) demonstrating both features.
- **T015** — The repository contains `src/data/ingest_pipeline.py`, but the file is truncated and shows no implementation of dynamic batch‑size adjustment or writing of `data/processed/predictions.csv`. Moreover, the required output file `data/processed/predictions.csv` is absent, so the pipeline’s validation step cannot be verified. The task therefore remains unfinished.
