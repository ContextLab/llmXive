# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No code, script, configuration, or documentation for a resource‑monitoring wrapper is present; the only artifacts shown relate to data ingestion, modeling, and reporting, not to CPU‑time or RAM enforcement. Consequently the required implementation of a monitoring wrapper that enforces the 6‑hour / 7 GB limits is missing.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_mg.csv
- **T015** — No code, script, or documentation showing the added DOI error‑handling logic is present; the implementer provided no artifact (e.g., updated ingestion module, unit test, or log output) that demonstrates a primary‑DOI fallback to a secondary DOI and a DATA_UNAVAILABLE halt when both fail. Consequently the requirement cannot be verified as met.
- **T018** — The required artifact `tests/unit/test_descriptors.py` does not exist on disk, so no unit test for the descriptor calculation logic is present. The task’s core deliverable is missing.
- **T024** — No evidence of an `artifacts/models/` directory with saved model files nor an `artifacts/metrics/` directory containing R², MAE, and feature importance data was provided. The required artifacts are missing, so the task is not satisfied.
- **T025** — No code, configuration, tests, or logs were provided that implement or demonstrate resource‑monitoring checks for runtime < 6 h and RAM < 7 GB. The required artifact (e.g., a monitoring script, CI guard, or runtime/RAM validation step) is missing, so the task is not satisfied.
