# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — No `tests/contract/` directory or any schema validator files (e.g., JSON/YAML schemas, Python validation scripts) are present in the provided evidence. Consequently, the required artifact for setting up dataset and model output validators is missing.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.parquet
- **T014b** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.parquet, data/processed/correlation_matrix.csv
- **T014c** — The repository does not contain the required `data/processed/descriptors_filtered.parquet` file, and the shown portion of `code/data/preprocess_2d.py` stops before any implementation of Pearson‑correlation filtering or writing a filtered matrix. Consequently the core logic (computing correlations, dropping features with |r| > 0.85, and saving the result) is absent.
- **T014d** — The required output files `data/processed/descriptors.parquet` and `data/processed/descriptors_no_filter.parquet` are missing, and the provided `preprocess_2d.py` does not contain any implementation of the “no‑filter” correlation logic nor a copy operation to create the `_no_filter` file. The task’s core requirement is therefore not satisfied.
