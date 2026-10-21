# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/02_feature_engineering.py` script and the output CSV `data/raw/descriptors_added.csv` exist and contain the required descriptor and fingerprint columns, but the accompanying unit test `code/tests/test_feature_engineering.py` fails to import the module (FileNotFoundError) and therefore does not verify the descriptor values as required. The broken test means the task’s verification step is not satisfied. Fix the test’s import path (or adjust the project layout) so the test can run and confirm the computed descriptors.
- **T003** — Requested task execution failed; rerun successfully: code/01_data_ingestion.py exit=1
