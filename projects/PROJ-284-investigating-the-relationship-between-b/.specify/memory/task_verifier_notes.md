# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires creating a specific project directory structure (`code/data`, `code/analysis`, `code/viz`, `code/report`, `code/tests`, `data/raw`, `data/processed`, `data/analysis`, `logs`, `docs`), but the evidence collector found no artifacts on disk — no directories or files were confirmed to exist at the project root. There is no evidence that the `mkdir -p` command was executed or that any of the required directories exist.
- **T003** — No artifacts were provided or confirmed on disk for this task — there is no evidence of a ruff configuration (e.g., `pyproject.toml`/`ruff.toml` with lint rules), formatter setup, or any lint/format execution logs. The task "Configure linting (ruff) and formatting tools" requires actual configuration files to exist, and none were shown.
- **T004** — `code/config.py` exists but contains only a `get_hcp_credentials()` helper; it defines none of the required configuration keys (`HCP_CREDENTIALS`, `BATCH_SIZE`, `MEMORY_LIMIT` (7GB), `HCP_API_VERSION`, `SCHAEFER_ATLAS_URL`, `PCA_COMPONENTS` (2)). The implementer must add these keys with the specified values (e.g., MEMORY_LIMIT = 7GB, PCA_COMPONENTS = 2) rather than just a credentials helper.
- **T004a** — declared artifact(s) missing/empty/invalid: pipeline_config.yaml
- **T006** — The task requires logging infrastructure writing structured logs to `logs/pipeline.log`, but the evidence collector found no artifacts at all — no logging module/code, no `logs/` directory, and no `pipeline.log` file exist in the project. There is nothing on disk to verify the claim against, so the task cannot be judged complete.
- **T056** — declared artifact(s) missing/empty/invalid: pipeline_dag.yaml, code/utils/pipeline_dag.yaml
- **T073** — declared artifact(s) missing/empty/invalid: code/utils/gpu_offload.py
- **T026** — Requested task execution failed; rerun successfully: code/analysis/power.py exit=1
- **T028** — declared artifact(s) missing/empty/invalid: code/utils/gpu_offload.py
