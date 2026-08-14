# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020b** — The provided `src/data/merge.py` is truncated (the `detect_aggregation_need` function is incomplete and no aggregation‑or‑write logic is visible), and the required output file `data/processed/species_aggregates.parquet` does not exist. Both the implementation and the generated artifact are missing.
- **T020c** — The `src/data/merge.py` file is truncated (e.g., an incomplete `detect_aggregation_need` definition) and does not contain logic that checks `needs_aggregation`, calls the analysis module on `data/processed/species_aggregates.parquet`, or writes `aggregated_results.csv`. Moreover, the required data files `data/processed/species_aggregates.parquet` and `data/processed/aggregated_results.csv` are missing. The task’s core functionality is therefore not implemented.
- **T028a** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, data/processed/merged_dataset.parquet, data/processed/tree.newick
- **T028b** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, data/processed/merged_dataset.parquet, data/processed/phylo_covariance_matrix.npy
- **T028c** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, data/processed/merged_dataset.parquet, data/processed/tree.newick, data/processed/phylo_covariance_matrix.npy
- **T029a** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
- **T029b** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
- **T030** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
