# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The `code/ingest.py` file contains placeholder functions (`fetch_dst_indices` returns an empty list and `write_dst_data` does nothing) and does not implement any logic to download Dst indices or write them to a CSV. Moreover, the required output file `data/raw/dst_indices.csv` is absent. The task’s core requirement—downloading Dst data and saving it to the specified CSV—is therefore not satisfied.
- **T013b** — The repository lacks the required `data/raw/kp_indices.csv` file, and the provided `code/ingest.py` contains only a stub for fetching Kp data without any logic to write the results to CSV or validate against a schema. The implementation is therefore incomplete.
- **T016** — No `aligned_events.csv` (or any derived file) containing the required `is_recurrent` flag was provided. The evidence lacks the primary dataset with the recurrent‑activity flag, so the task’s core requirement is not demonstrated.
- **T016b** — declared artifact(s) missing/empty/invalid: data/processed/analysis_subset.csv
- **T018** — The repository contains a `code/validate.py` with a validation function, but the required schema file `contracts/aligned_event.schema.yaml` is missing, so the validation cannot actually be performed. Moreover, there is no evidence that the validation result is used to prevent writing `aligned_events.csv` or updating `data/source_manifest.yaml`. Both the schema and the blocking integration are absent.
- **T017** — The required file `data/processed/aligned_events.csv` does not exist, and the `data/source_manifest.yaml` still shows the aligned_events entry with status “Pending” and no checksum values. Both the CSV output and the manifest updates are missing.
- **T019** — No code, configuration, or log output was provided showing that data‑quality metrics (e.g., counts of missing CME speeds, missing flare entries, etc.) are being logged. Without an artifact demonstrating the added logging, the requirement cannot be confirmed as satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T023b** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T025** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T026** — declared artifact(s) missing/empty/invalid: results/metrics.json
