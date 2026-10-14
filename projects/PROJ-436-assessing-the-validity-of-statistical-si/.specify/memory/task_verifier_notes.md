# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — I inspected `code/data_loader.py`, `code/config.py`, and the test logs. The loader tries to read OpenML parquet files but the environment lacks a parquet engine (pyarrow/fastparquet), causing `DataLoadError` on every dataset. The unit tests fail, and the generated `data/checksums/manifest.json` is empty (no checksum entries). Consequently the loader does not successfully download, validate, and record checksums for the required datasets, nor does it demonstrate the MNAR synthetic‑outcome logging. The task therefore remains unfinished.
- **T102** — Requested task execution failed; rerun successfully: code/main_us1.py exit=1
