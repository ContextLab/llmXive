# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The collector shows that `data/raw/` and `data/processed/` directories are missing (and therefore their required empty `__init__.py` files are absent), violating the task’s specification to create those directories and init files.
- **T003** — The `code/.ruff.toml` file exists and sets `line-length = 88`, but its `select` list contains additional codes (`"W"`, `"B"`, `"C4"`, `"UP"`) beyond the required `["E", "F", "I"]`, so it does not match the exact specification. The `code/pyproject.toml` correctly includes `[tool.black] line-length = 88`. The mismatch in the Ruff configuration makes the task incomplete.
- **T004** — The provided `code/config.py` contains all required constants except `BASELINE_HASH`; this variable is absent, so the task’s specification is not fully met. Adding a line such as `BASELINE_HASH = "sha:abc123..."` would complete the requirement.
- **T005** — The `code/data_loader.py` file exists and streams the ALFWorld dataset using `datasets.load_dataset(..., streaming=True)`, but it does **not** implement any checksum verification of the downloaded data, which is a core requirement of the task. Adding hash/checksum validation for the streamed files is needed to satisfy the specification.
- **T024** — declared artifact(s) missing/empty/invalid: tests/integration/test_gpu_free.py
- **T032** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
