# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The required file `tests/unit/test_classification.py` does not exist, so no unit test for the negation‑aware keyword classification logic is present. The task’s deliverable is missing entirely.
- **T012** — The required artifact `tests/unit/test_anonymization.py` does not exist on disk, so no unit test for PII anonymization is provided. The task cannot be considered completed until the file is created with appropriate tests.
- **T015b** — No code, log output, or comment indicating that a CPU feasibility analysis for FR‑002c was performed (or that the feature was deferred) is present. The required artifact—a file containing the feasibility check logic or a comment/log entry “FR‑002c Deferred”—is missing.
- **T017** — The required output files `data/processed/anonymized.csv` and `data/processed/raw_counts.json` are absent, and the provided `code/01_ingest.py` contains numerous placeholder functions and is truncated, showing no logic that actually writes those files. The implementation does not fulfill the task’s requirement to save the specified artifacts.
- **T019** — declared artifact(s) missing/empty/invalid: tests/integration/test_ingest_pipeline.py
- **T020** — The required file `tests/unit/test_lexicon.py` does not exist, so no unit test for the `prosocial_action_count` lexicon logic is present. The task cannot be considered done until the test file is created with appropriate test cases.
- **T021** — The required artifact `tests/unit/test_vader.py` does not exist on disk, so no unit test for VADER `neg_score` extraction and range validation is present. The task cannot be considered completed until this file is created with appropriate tests.
