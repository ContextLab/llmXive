# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: src/utils/checksum_all.py exit=1
- **T003** — The required outputs `data/processed/features.csv` and `data/processed/featurize.log` are MISSING, so the featurization was never successfully run. The only existing output, `descriptor_gaps.log`, records a detected gap ("Row 0 (BaTiO3): missing A_atomic_radius"), meaning the script aborted with "Descriptor gaps detected" rather than producing the feature matrix — the verification requirement (12 descriptor columns + formation_energy, no missing targets) cannot be checked against any actual CSV. The implementer must fix the descriptor computation (e.g., the atomic-radius fallback) and re-run t
- **T004** — The required output `data/processed/validation.log` is MISSING — the script `src/data/validate.py` exists and looks correct, but there is no evidence it was ever executed, so no log with row count, power estimate, or warnings exists. The implementer must run the validation script (with `data/processed/features.csv` present) to produce the log.
- **T005** — Requested task execution failed; rerun successfully: src/utils/checksum_all.py exit=1
