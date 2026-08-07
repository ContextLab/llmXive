# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The provided `models.py` defines a `Subject` class with validation logic, but the file is truncated and does not include the required `ConnectivityMatrix` class. Moreover, the referenced schema file `contracts/subject.schema.yaml` is missing, so validation cannot actually be performed. Both the missing model and schema prevent the task from being fully satisfied.
- **T013** — The `test_full_ingestion` function in `tests/integration/test_ingestion.py` does not contain the required assertions `assert os.path.exists('data/processed/subjects_cleaned.csv')` and `assert len(pd.read_csv('data/processed/subjects_cleaned.csv')) == 10`. Additionally, the expected output file `data/processed/subjects_cleaned.csv` is not present. The task’s specification is therefore not satisfied.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/subjects_cleaned.csv
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/connectivity_results.csv
- **T031** — declared artifact(s) missing/empty/invalid: data/processed/nbs_results.csv
