# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T027** — The required output files `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy` are absent, and the provided `src/analysis/phylogeny.py` is incomplete (truncated) with no implementation of Maximum Likelihood tree construction or writing of the specified artifacts. The task’s core requirements are therefore not met.
- **T028b** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, data/processed/merged_dataset.parquet, data/processed/tree.newick, data/processed/raw_correlations.csv
- **T029** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py, data/processed/raw_correlations.csv, data/processed/adjusted_pvalues.csv
- **T031b** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
- **T059** — The required `src/utils/errors.py` file does not exist, and `src/analysis/correlation.py` is missing entirely. Moreover, the existing `src/data/download.py` does not define or use a `DataFetchError` nor implement the unified error‑handling pattern described in the task. The implementation therefore fails to meet the core requirements.
