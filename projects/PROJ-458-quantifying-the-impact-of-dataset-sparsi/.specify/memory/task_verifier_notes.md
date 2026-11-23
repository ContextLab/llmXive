# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/requirements.txt` file exists and contains pinned versions, but there is no evidence (e.g., command output, logs, or a lock file) showing that `pip install -r code/requirements.txt` actually runs successfully without version conflicts. The verification step is missing.
- **T003** — declared artifact(s) missing/empty/invalid: commit-config.yaml
- **T004** — The provided `code/config.py` implements the `load_env()` function and correctly raises a `RuntimeError` when `MP_API_KEY` is absent (as shown by the passing unit test), but it does **not** define any pipeline constants such as `SEED_LIST` or `SPARSITY_LEVELS` that the task explicitly requires. Adding these constant definitions is needed to meet FR‑001.
- **T020** — Requested task execution failed; rerun successfully: code/data_ingestion.py exit=1
