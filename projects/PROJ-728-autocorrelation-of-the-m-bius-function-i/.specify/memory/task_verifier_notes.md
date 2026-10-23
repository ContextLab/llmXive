# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The `data/processed/window_index.csv` file has the correct number of rows and passes the non‑overlap test, but the unit test for SHA‑256 reproducibility fails (the generated hash does not match the expected deterministic hash). Therefore the output is not reliably deterministic as required. Fix the window generation to produce a reproducible CSV (e.g., ensure the same RNG sequence and ordering) so the SHA‑256 hash matches on repeated runs.
- **T005** — Requested task execution failed; rerun successfully: code/demo_autocorr.py exit=1
