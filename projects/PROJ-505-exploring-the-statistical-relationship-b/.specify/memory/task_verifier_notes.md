# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The `code/utils/io.py` file implements MD5 checksum helpers (`compute_md5`, `verify_md5`) instead of the required SHA‑256 checksum function, so it does not meet the specification. The `code/utils/logging.py` only provides a `get_logger(name)` factory and does not create a module‑level logger (`logging.getLogger(__name__)`) at import time as required. These mismatches mean the task’s functional requirements are not satisfied.
- **T005** — Requested task execution failed; rerun successfully: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1
