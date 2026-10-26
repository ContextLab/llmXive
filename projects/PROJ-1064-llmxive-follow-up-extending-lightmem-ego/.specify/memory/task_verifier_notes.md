# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/data/download.py exit=1; src/data/preprocess.py exit=1
- **T002** — The `src/data/preprocess.py` script exists and appears to implement the required logic, and a parquet file `data/processed/memory_nodes.parquet` was generated without error. However, the provided evidence does not include any concrete verification that the parquet file actually contains ≥ 100 rows, that all required columns (`node_id`, `timestamp`, `event_label`, `embedding`, `is_rare`) are present, or that the `is_rare` column shows both `True` and `False` values. Without this explicit validation output, the task’s verification criteria are not satisfied.
- **T003** — Requested task execution failed; rerun successfully: src/data/faiss_builder.py exit=1
