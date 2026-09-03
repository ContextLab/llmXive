# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012b** — declared artifact(s) missing/empty/invalid: data/raw/study_manifest.json
- **T012c** — declared artifact(s) missing/empty/invalid: data/raw/filtered_study_manifest.json
- **T013** — The repository contains `code/data/validate_temporal.py`, but the file is truncated in the view and there is no `data/processed/temporal_validation_log.json` produced (the file is missing). Since the required output log is absent (and the script’s full logic/exit‑code handling cannot be verified), the task is not fully satisfied.
- **T014a** — declared artifact(s) missing/empty/invalid: data/processed/heterogeneity_report.json
- **T014b** — The repository contains `code/data/harmonize.py`, but the required input file `data/processed/heterogeneity_report.json` is missing, so the script cannot run as specified. Additionally, the provided source is truncated, leaving the implementation incomplete. The task’s prerequisite and required artifact are not satisfied.
- **T017a** — The required output files `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv`, and `data/processed/preprocess_log.json` are absent from the repository, so the preprocessing pipeline was not executed to completion. The implementer must run `code/data/preprocess.py` and ensure these non‑empty files are created and their SHA256 checksums recorded.
