# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml` with Black settings, `.flake8` or equivalent) or related setup scripts are present in the `code/` directory, so the requirement to configure Black and Flake8 is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty.
- **T014** — No code, script, or data artifact was provided that implements the required sorting logic, applies `CONFIG.RETENTION_PCT` to select the cutoff, or produces the “Critical Sub-network” candidate list. The evidence lacks any implementation or output file, so the task’s requirement is not satisfied.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/pruned_model_weights.pt
- **T019** — The `code/03_finetune_pruned.py` file is truncated (ends mid‑function) and does not contain a complete fine‑tuning implementation, nor does it show usage of a low learning rate or deterministic sampling via `CONFIG.SAMPLE_SEED`. Additionally, the required dataset `data/raw/occ_rag_corpus.jsonl` is absent, so the script cannot draw examples as specified. Both the script and the input data are missing/unfinished.
