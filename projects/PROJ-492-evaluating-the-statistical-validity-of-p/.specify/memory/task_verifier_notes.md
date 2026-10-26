# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The `data/input/urls.csv` passes the minimum‑row test, but `data/raw/` is empty (0 entries) and the pytest suite reports missing HTML files for the URLs. Consequently the required raw HTML snapshots are not present, and the checksum file lists hashes for files that do not exist. The corpus is therefore not fully materialised.
- **T004** — Requested task execution failed; rerun successfully: code/src/audit/monte_carlo_validation.py exit=1
