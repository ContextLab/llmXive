# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
- **T002** — The required output Parquet file `data/processed/document_pairs.parquet` does not exist, and the unit test `tests/unit/test_preprocess.py` fails because the sample data directory is missing, indicating the preprocessing script has not been successfully run and verified. The contract test file is present but only checks schema validity, not the actual data generation. The missing Parquet artifact and failing unit test must be fixed.
- **T003** — Requested task execution failed; rerun successfully: src/data/latent_generator.py exit=1
