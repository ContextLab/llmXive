# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — The repository lacks the required `data/raw/bronze.parquet` file and the state YAML still contains `data_raw_bronze: null`, indicating the checksum was never written. Moreover, `code/ingest.py` defines but never uses `compute_sha256` and does not invoke `update_state_artifact_hash` to atomically record the hash. The download‑to‑parquet conversion and state update steps are therefore not implemented.
- **T007b** — declared artifact(s) missing/empty/invalid: data/raw/bronze.parquet
- **T063** — The required artifact `data/raw/bronze.parquet` does not exist on disk, so the download logic and fallback handling have not been demonstrated. The task’s primary output is missing, indicating the implementation is not complete.
- **T064** — The repository lacks the required `data/processed/preprocess_stats.json` file, and the shown portion of `code/preprocess.py` does not contain an `init_preprocess_stats()` function that writes this JSON file. Consequently, the task’s core output and behavior are missing.
