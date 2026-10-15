# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — Checked the repository for the required directories (`code/models`, `code/data`, `code/experiments`, `code/config`, `code/tests`) and the corresponding `__init__.py` files; no such paths or files were present in the collected artifact list. The task’s directory structure and package markers are therefore missing.
- **T001b** — The evidence provided does not show the existence of the required directories (`artifacts/logs`, `artifacts/checkpoints`, `artifacts/results`, `state`, `data/raw`, `data/processed`). Since no confirmed artifacts confirm that these paths were created, the task requirement is not satisfied.
- **T002** — Checked the `requirements.txt` file (exists, correct pinned versions plus extra packages). However, there is no evidence that `pip install -r requirements.txt` was executed and succeeded (no command output, logs, or test results). The verification step required by the task is missing.
- **T003** — declared artifact(s) missing/empty/invalid: pyproject.toml
- **T005** — declared artifact(s) missing/empty/invalid: code/models/utils.py
- **T006** — declared artifact(s) missing/empty/invalid: code/data/loaders.py
- **T007** — declared artifact(s) missing/empty/invalid: code/models/transformer_base.py
- **T008** — declared artifact(s) missing/empty/invalid: code/experiments/utils.py
- **T009** — the task writes platform-owned path(s) inside the project: `state/artifact_hashes.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T014** — declared artifact(s) missing/empty/invalid: code/models/utils.py
- **T011** — declared artifact(s) missing/empty/invalid: code/models/transformer_dendritic.py
- **T013** — declared artifact(s) missing/empty/invalid: code/experiments/validate_arch.py
- **T015** — The evidence contains no code, configuration, or documentation showing that logging has been consolidated, that T013 now serves as the sole source of truth for architecture‑match validation, or that any redundant logging tasks have been removed. No artifact paths or files were provided to verify these changes, so the requirement is unmet.
- **T010** — declared artifact(s) missing/empty/invalid: tests/test_architecture.py
- **T017** — The required artifact `tests/test_training.py` is reported as MISSING, so the integration test for the timeout mechanism does not exist in the project. Without this file the task’s requirement cannot be satisfied.
- **T018** — Requested task execution failed; rerun successfully: code/experiments/train.py exit=1; code/utils/download_data.py exit=1
- **T043** — declared artifact(s) missing/empty/invalid: tests/unit/
