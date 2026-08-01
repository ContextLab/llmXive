# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T031b** — The required schema file `contracts/session.schema.yaml` is missing, so there is nothing for the simulator to validate against. Moreover, the provided `simulator.py` snippet only imports validation utilities but does not show any actual call to `load_schema` or `validate_session` on the generated sessions. Both the schema artifact and concrete validation implementation are absent.
- **T021a** — The repository contains `code/analysis/data_cleaner.py`, but the file is truncated and does not show the full implementation (e.g., the cleaning, imputation, and CSV export logic). Moreover, the required output file `data/processed/cleaned_sessions.csv` is absent. Without a generated cleaned CSV, the task’s deliverable is not met.
- **T036b** — declared artifact(s) missing/empty/invalid: data/processed/power_report.md
