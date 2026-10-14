# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — `code/data_loader.py` and `code/config.py` exist and look substantive, but `data/checksums/manifest.json` contains only `{"datasets": {}}` — no dataset was ever successfully downloaded, checksummed, or recorded, and there are no raw CSVs under `data/raw/` or any log evidence showing a real fetch, the N<100 skip logic, or the synthetic-outcome generation actually firing. The verification criteria (manifest populated with SHA256 checksums for datasets 42803/43844/43845, synthetic-outcome action recorded in logs, import succeeding) are unmet; the loader was written but never demonstrably executed
- **T102** — Requested task execution failed; rerun successfully: code/main_us1.py exit=1
