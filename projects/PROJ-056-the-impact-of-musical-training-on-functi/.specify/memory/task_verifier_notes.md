# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The `code/data/models.py` file is present but the `ConnectivityMatrix` class definition is cut off (truncated after `if self.matrix.ndim !=`) and the required `contracts/subject.schema.yaml` file does not exist, so the validation cannot be verified against the specified schema. The task’s mandatory artifacts are therefore missing or incomplete.
- **T013** — The provided `tests/integration/test_ingestion.py` defines `test_full_ingestion`, but it checks a temporary file (`tmp_path / "subjects_cleaned.csv"`) instead of asserting the existence of `'data/processed/subjects_cleaned.csv'` as required, and therefore does not contain the exact assertions specified in the task. Moreover, the expected output file `data/processed/subjects_cleaned.csv` is missing from the repository. The task’s requirement is not genuinely satisfied.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/subjects_cleaned.csv
