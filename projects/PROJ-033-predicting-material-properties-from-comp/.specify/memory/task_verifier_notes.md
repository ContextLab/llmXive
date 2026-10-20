# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required contracts, requirements.txt, seeds utility, and quickstart.md are present and correctly populated, but there is no evidence that `pytest tests/contract/` was executed and passed as the task demands. Without test‑run output confirming the contract tests succeed, the verification step is incomplete.
- **T002** — Checked `data/raw/materials.csv` (columns present, checksum recorded in README) and the schema test file, but there is no evidence that `pytest tests/contract/test_dataset_schema.py` was actually executed and passed; only a custom script log is provided. The required pytest validation step is missing.
- **T003** — The `src/data/loader.py` implementation fails several required unit‑test checks: the zero‑band‑gap metal (`m09`) is dropped, the outlier‑removal log reports “dropped 2” rows instead of the expected “dropped 1”, and the summary shows only 8 rows kept rather than the 9 valid rows. Consequently the loader does not meet the specification for outlier handling and logging.
- **T006** — Requested task execution failed; rerun successfully: src/training/train_gnn.py exit=1; src/training/evaluate.py exit=1
