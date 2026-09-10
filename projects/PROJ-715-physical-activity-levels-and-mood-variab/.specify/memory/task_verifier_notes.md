# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — `code/ingest.py` is present but the shown implementation never calls `compute_sha256` after download, does not write the checksum before any file write, and the `extract_and_convert_zip` function is truncated and does not produce `data/raw/bronze.parquet`. The required `data/raw/bronze.parquet` file is missing, and the state YAML still has `data_raw_bronze: null` instead of the SHA‑256 hash. The critical integrity steps and atomic state update are therefore not fulfilled.
- **T007b** — declared artifact(s) missing/empty/invalid: data/raw/bronze.parquet
- **T063** — The required artifact `data/raw/bronze.parquet` does not exist on disk, so the download logic and fallback handling have not been demonstrated. The task’s primary output is missing, indicating the implementation is not complete.
