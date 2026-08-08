# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006b** — The provided `code/downloaders.py` only contains a partially‑implemented OQMD download function, lacks any AFLOW download logic, does not include fallback URL handling, and the required output files `data/raw/oqmd.parquet` and `data/raw/aflow.parquet` are absent. The implementation therefore does not meet the task specifications.
- **T006d#1** — The repository does not contain `data/raw/mp.parquet`, and the shown `code/downloaders.py` lacks any implementation that checks for a Materials Project API key and downloads the MP dataset to that path (the file is truncated before any MP‑specific logic). Consequently the required dataset file is absent and the module does not fulfill the specified behavior.
