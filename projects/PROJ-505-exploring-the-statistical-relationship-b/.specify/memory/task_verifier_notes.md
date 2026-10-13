# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The `code/utils/io.py` and `code/utils/logging.py` files contain the required functions, but the package’s `code/utils/__init__.py` tries to import non‑existent `compute_md5` and `verify_md5`, causing import errors and preventing the unit tests from running. The failing imports must be corrected (e.g., import `compute_sha256`/`verify_sha256` or remove the mismatched imports) for the tests to execute and pass.
- **T005** — Requested task execution failed; rerun successfully: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1
- **T006** — Requested task execution failed; rerun successfully: code/ingestion/generate_synthetic_data.py exit=1
