# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — The `code/data_loader.py` exists but it silently skips datasets on conversion errors instead of raising an exception, leaving `data/checksums/manifest.json` empty and never logging synthetic‑outcome generation (no dataset reached that branch). Consequently the loader does not “fail loudly” on fetch errors, does not record checksums for the required datasets, and does not demonstrate the MNAR edge‑case handling in the logs.
- **T102** — Requested task execution failed; rerun successfully: code/main_us1.py exit=1
