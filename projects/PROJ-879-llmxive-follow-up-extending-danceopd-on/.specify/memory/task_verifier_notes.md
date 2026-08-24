# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No evidence of the required files (`code/main.py`, `code/00_data_fetch.py`, `code/00_data_stream.py`, `code/00_teacher_inference.py`, `code/01_train_trees.py`, `code/02_evaluate_fidelity.py`, `code/03_versioning.py`) was provided; the claim lacks any artifact listing or file contents to confirm they exist and are non‑empty. The implementer must add these seven Python files in the `code/` directory.
- **T014** — The `data/processed/teacher_routing_dataset.parquet` file does not exist, and the provided `code/00_data_extraction.py` is truncated and lacks any logic that writes the extracted columns to that Parquet file. Consequently, the required extraction and streaming step is not implemented.
- **T020** — The `code/01_train_trees.py` file is truncated (the `split_data` function ends abruptly) and thus does not contain a complete, runnable data‑splitting implementation. Moreover, the required input file `data/processed/teacher_routing_dataset.parquet` is absent, so the code cannot be exercised as specified. Both the missing dataset and the incomplete script must be provided/fixed.
- **T031** — declared artifact(s) missing/empty/invalid: code/data/generate_teacher.py
