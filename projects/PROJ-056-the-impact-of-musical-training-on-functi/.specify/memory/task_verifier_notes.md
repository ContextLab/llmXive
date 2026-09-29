# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The `Subject` model with the required attributes and custom validation is present, but the referenced `contracts/subject.schema.yaml` file is missing, so the validation cannot be verified against the actual schema. The task’s mandatory requirement to ensure instances match that schema is therefore not satisfied. Provide the missing schema file (or load it in the validation logic) to complete the task.
- **T013** — The provided `tests/integration/test_ingestion.py` defines `test_full_ingestion`, but it checks a temporary file (`tmp_path / "subjects_cleaned.csv"`) instead of asserting the existence of `'data/processed/subjects_cleaned.csv'` as required, and therefore does not contain the exact assertions specified in the task. Moreover, the expected output file `data/processed/subjects_cleaned.csv` is missing from the repository. The task’s requirement is not genuinely satisfied.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/subjects_cleaned.csv
- **T038** — No `correlation_results.csv` (or any updated file) was provided, and there is no evidence that a `stability_flag` column was added to flag low stability when the 95 % CI includes zero at any of the swept thresholds. The required output artifact is missing.
- **T039** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T040** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.csv
- **T041** — No `quickstart.md` file or excerpt showing the required documentation updates (how to run verification vs analysis mode) was provided. Without the actual markdown content, the claim cannot be verified as fulfilled. The implementer must supply the updated `quickstart.md` with the specified instructions.
