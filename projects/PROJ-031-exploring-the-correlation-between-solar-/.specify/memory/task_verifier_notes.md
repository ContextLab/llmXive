# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013b** — The repository contains a partially‑implemented `code/ingest.py`, but the script does not include a complete function that fetches the Kp index data and writes it to `data/raw/kp_indices.csv`, and the expected CSV file is absent from the project. Consequently the required artifact and its validation are missing.
- **T016** — No `aligned_events.csv` (or any derived file) containing the required `is_recurrent` flag was provided. The evidence lacks the primary dataset with the recurrent‑activity flag, so the task’s core requirement is not demonstrated.
- **T018** — The repository lacks the required `contracts/aligned_event.schema.yaml` (the schema file is missing), so `code/validate.py` cannot actually validate the CSV. Moreover, the provided `validate.py` only defines validation functions and does not contain any logic that prevents writing `aligned_events.csv` or updating `data/source_manifest.yaml` when validation fails. Both the essential schema and the blocking behavior are absent.
- **T019** — No code, configuration, or log output was provided showing that data‑quality metrics (e.g., counts of missing CME speeds, missing flare entries, etc.) are being logged. Without an artifact demonstrating the added logging, the requirement cannot be confirmed as satisfied.
- **T023** — No code, notebook, data file, or result output was provided that shows a linear regression model with flare and CME as separate predictors nor any calculated R² values. The claim lacks any tangible artifact to verify the analysis was performed.
- **T024** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T023b** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T025** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T026** — declared artifact(s) missing/empty/invalid: results/metrics.json
