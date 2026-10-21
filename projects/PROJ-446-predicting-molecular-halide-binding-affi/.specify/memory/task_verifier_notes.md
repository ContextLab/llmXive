# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The unit test `code/tests/test_feature_engineering.py` fails to import `02_feature_engineering.py` (FileNotFoundError), so the required test that validates descriptor values never runs. Consequently the task’s verification step—checking correct descriptor computation for known SMILES—is not satisfied. The test path logic must be corrected and the test must pass, confirming that the generated `descriptors_added.csv` contains the proper rows and descriptor values.
- **T003** — Requested task execution failed; rerun successfully: code/01_data_ingestion.py exit=1
