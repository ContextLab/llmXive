# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The implementer provided only a claim placeholder and no actual artifacts (no code, dataset, computed metrics, or analysis results). Required outputs such as a data ingestion pipeline, per‑node `bridging_coefficient` and `primary_cluster` values, citation counts, novelty scores, and the correlation/regression analysis are missing.
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/subgraph_with_clusters.parquet
- **T023** — The required source file `src/services/embeddings.py` does not exist, and the log file `data/logs/excluded_nodes.csv` is also missing, so the edge‑case handling and logging specified in the task have not been implemented. The next implementer must create/modify the embeddings module and generate the CSV log.
- **T020** — declared artifact(s) missing/empty/invalid: src/services/embeddings.py
- **T022** — No code, data files, or computed results were supplied; there is no implementation that computes title embeddings, derives topic‑cluster centroids, or calculates cosine‑distance novelty scores as required. Consequently the task’s deliverable (a functional novelty‑score calculation) is missing.
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/final_analysis_dataset.parquet
- **T037** — The required file `tests/integration/test_statistical_pipeline.py` does not exist, so the integration test with `test_binned_analysis_execution` is missing entirely. No evidence of the requested test implementation is present.
- **T028** — No code, script, or documentation was provided that implements a multiple‑comparison correction (Bonferroni or Benjamini‑Hochberg) nor a CLI flag to select the method. Without such artifacts, the requirement is not satisfied.
- **T029** — declared artifact(s) missing/empty/invalid: results/analysis_report.md
- **T030** — declared artifact(s) missing/empty/invalid: results/statistical_metrics.json
- **T031** — No evidence of the `specs/001-bridging-coefficient-analysis/quickstart.md` file or its updated “Prerequisites” and “Run” sections is provided; without the actual documentation changes, we cannot verify that the required updates were made. The implementer must supply the modified markdown file showing the final pipeline steps, dependencies, and exact CLI commands.
