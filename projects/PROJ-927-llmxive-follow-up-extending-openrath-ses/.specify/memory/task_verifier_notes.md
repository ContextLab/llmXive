# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The required directories `data/processed/corrupted_logs/`, `data/processed/reconstruction_results/`, and `scripts/` are missing, even though all `__init__.py` files in the `code/` subfolders are present. The task is not fully satisfied until these directories are created.
- **T001b** — The `code/simulators/` directory exists, but there is no evidence shown that `__init__.py` is empty as required; the file’s contents were not provided. The implementer must supply the content of `__init__.py` (or a statement confirming it is empty) to satisfy the task.
- **T001c** — declared artifact(s) missing/empty/invalid: data/processed/corrupted_logs/, data/processed/reconstruction_results/
- **T002** — The `requirements.txt` file exists at the required path and contains the exact versions for `pytest`, `scipy`, `pyyaml`, `jsonschema`, and `ruff`, but it also includes additional packages (`pydantic`, `numpy`, `matplotlib`) that were not part of the task specification. The task required only the listed dependencies to be pinned, so the artifact does not precisely match the requirement.
- **T003** — The provided `pyproject.toml` correctly contains a `[tool.black]` section with `line-length = 88`, but the `.ruff.toml` does not satisfy the linting requirement: it lists `E501` in the `ignore` list (disabling the rule) and does not explicitly enable `F401` and `W293` as the task specifies. The file must be edited to select those three rules (and not ignore `E501`).
- **T009** — The repository contains a non‑empty `code/main.py` with the required `--seed`, `--count`, and `--resume` arguments and a checkpoint YAML file that includes `last_workflow_id` and `status`. However, the checkpoint logic only records a single `last_workflow_id`/`status` pair and does not distinguish between the generation (US1) and execution (US2) phases, so it cannot reliably resume each phase independently if an interruption occurs. The implementation needs per‑phase or per‑workflow phase tracking in the checkpoint to satisfy the “must support resuming both the generation phase and the executi
- **T006b** — declared artifact(s) missing/empty/invalid: code/generators/schemas.py
- **T026-Exec** — declared artifact(s) missing/empty/invalid: data/processed/corruption_map.json
- **T026a** — declared artifact(s) missing/empty/invalid: code/simulators/schemas.py
- **T030** — declared artifact(s) missing/empty/invalid: code/reconstructors/reconstruction_engine.py
- **T034a** — declared artifact(s) missing/empty/invalid: code/analyzers/statistical_test.py, data/processed/results/aggregated_metrics.json
- **T034b** — declared artifact(s) missing/empty/invalid: code/analyzers/statistical_test.py
- **T034c** — declared artifact(s) missing/empty/invalid: code/analyzers/statistical_test.py
- **T038** — declared artifact(s) missing/empty/invalid: code/analyzers/statistical_test.py
- **T044a** — declared artifact(s) missing/empty/invalid: tests/unit/test_config.py
