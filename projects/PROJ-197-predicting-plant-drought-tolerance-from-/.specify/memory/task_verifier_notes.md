# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory tree (code/, data/raw/, data/processed/, tests/, docs/, docs/reports/) is presented; the implementer did not provide any file‑system listing, screenshots, or other proof that these folders exist and are non‑empty. The task therefore remains unverified.
- **T016** — The repository contains a `generate.py` with a correct `generate_synthetic_phylogenetic_matrix` function, but the script never writes the resulting matrix to `data/processed/synthetic_phylo_matrix.npy`, and that file is absent from the project. The required output file is missing, so the task is not fully satisfied.
- **T012** — The repository contains a `code/data/generate.py` file, but it is truncated and does not show the required logic for creating the 20‑gene synthetic features, applying the label rule (`sum >= 12`), or writing the result to `data/processed/synthetic_genomics.csv`. Moreover, the expected output CSV file is absent from the `data/processed` directory. The required artifact is missing, so the task is not fulfilled.
- **T018** — declared artifact(s) missing/empty/invalid: tests/integration/test_train.py
- **T019** — declared artifact(s) missing/empty/invalid: tests/unit/test_stats.py
