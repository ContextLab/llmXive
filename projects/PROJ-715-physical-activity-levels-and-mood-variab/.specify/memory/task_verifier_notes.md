# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — The repository lacks the required `data/raw/bronze.parquet` file and the state YAML still contains `data_raw_bronze: null`, indicating the hash was never written. Moreover, the provided `code/ingest.py` is truncated, never calls `compute_sha256` after download, and does not invoke `update_state_artifact_hash` to record the checksum. The critical integrity steps are therefore not implemented.
- **T007b** — declared artifact(s) missing/empty/invalid: data/raw/bronze.parquet
- **T063** — The required artifact `data/raw/bronze.parquet` does not exist on disk, so the download logic and fallback handling have not been demonstrated. The task’s primary output is missing, indicating the implementation is not complete.
- **T064** — The `code/preprocess.py` file contains a partially‑written `init_preprocess_stats` function that is truncated (the `json.dump` call is incomplete and the function never finishes or verifies the file). Moreover, the required output file `data/processed/preprocess_stats.json` does not exist on disk. The task’s core requirement—creating the function and actually writing a non‑empty JSON file—is therefore not met.
