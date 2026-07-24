# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T082** — The `src/code/ingest.py` file does not contain a per‑request `timeout=10` (it defines `MB_TIMEOUT = 30` and uses the `musicbrainzngs` library, not `requests`), nor does it implement a global 300‑second batch timeout, log a “TIMEOUT_EXCEEDED” warning, write `partial_metadata_mpd.parquet`, or exit with code 1. Additionally, the required `data/derived/partial_metadata_mpd.parquet` file is missing.
