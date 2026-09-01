# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The implementer provided only a claim placeholder and no actual artifacts (no code, dataset, computed metrics, or analysis results). Required outputs such as a data ingestion pipeline, per‑node `bridging_coefficient` and `primary_cluster` values, citation counts, novelty scores, and the correlation/regression analysis are missing.
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/subgraph_with_clusters.parquet
- **T023** — The required source file `src/services/embeddings.py` does not exist, and the log file `data/logs/excluded_nodes.csv` is also missing, so the edge‑case handling and logging specified in the task have not been implemented. The next implementer must create/modify the embeddings module and generate the CSV log.
- **T032b** — The required file `src/services/embeddings.py` does not exist in the repository, so no refactored code implementing strict batch processing and memory release can be verified. The task’s core artifact is missing.
- **T039** — The `src/services/ingest.py` file shows no import or usage of `memory_profiler` and does not log peak RAM usage per batch. Additionally, the required `src/services/embeddings.py` file is completely missing. Both files need the memory‑profiling integration and the embeddings module must exist.
- **T038** — No `artifacts/validation_report.md` file was provided; thus there is no evidence of an execution log, exit code, or artifact hashes, which are required to satisfy the task. The implementer must generate and supply the validation report at the specified path.
