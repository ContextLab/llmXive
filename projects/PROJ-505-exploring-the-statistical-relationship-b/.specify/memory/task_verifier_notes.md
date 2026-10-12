# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` file exists, but it contains an extra line (`pyarrow>=12.0.*`) that does not follow the required `package==major.minor.*` pattern, violating the task’s specification. The file must be limited to the six listed packages, each pinned with `==` and a wildcard minor version.
- **T004** — The provided `code/utils/io.py` defines `compute_md5` that actually returns a SHA‑256 hash (64‑char hex) and the wrapper `utils/io.py` tries to import non‑existent `compute_sha256`/`verify_sha256`, causing an import error. Moreover, the unit test expects a 32‑character MD5 checksum, which the current implementation does not produce. The I/O helpers therefore do not pass the supplied tests.
- **T005** — Requested task execution failed; rerun successfully: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1
- **T006** — Requested task execution failed; rerun successfully: code/ingestion/generate_synthetic_data.py exit=1
