# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Checked `projects/PROJ-505-exploring-the-statistical-relationship-b/requirements.txt`. While all required packages are present with the correct `==major.minor.*` format, the file also contains an extra line `pyarrow>=15.0.0` that does not match the required pattern, violating the task’s specification. The extra, non‑pinned entry must be removed or changed to the proper pinned format.
- **T004** — The `code/utils/io.py` module exists, but its `save_parquet` function forces the use of the `pyarrow` engine, which is not available (ImportError shown in the test logs). Consequently the unit tests `test_save_and_load_parquet` and `test_sha256_checksum_and_verification` both fail, so the required I/O helpers do not reliably create and read Parquet files as specified. The logger module passes its tests. Fix the I/O helpers (e.g., make `pyarrow` optional or use a fallback engine) and ensure the tests pass.
- **T005** — Requested task execution failed; rerun successfully: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1
- **T006** — Requested task execution failed; rerun successfully: code/ingestion/generate_synthetic_data.py exit=1
