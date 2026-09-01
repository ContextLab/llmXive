# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — No `tests/unit/` or `tests/integration/` directories (with `__init__.py` files) were presented in the provided evidence, so the required test infrastructure is missing. The implementer must create the two directories and include the necessary `__init__.py` files.
- **T016** — No code, configuration, or test artifacts were provided showing that the dataset checksum is validated against `config.EXPECTED_AFLOW_CHECKSUM` or that exponential backoff with up to 3 retries is implemented. The required implementation and evidence are missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/true_novel.csv
- **T021** — The required output file `data/processed/heas_train_features.csv` does not exist, so the weighted mean/variance descriptors are not produced. Additionally, the provided `code/feature_engineering.py` is truncated and does not show the implementation that writes the required CSV with the specified columns. The task’s core deliverable is therefore missing.
