# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The provided `src/utils/atlas.py` exists but it caches files in `data/cache/` (not `data/atlas/`), never extracts a zip archive, and its API uses internal keys like `"schaefer_400"` rather than the required name string (e.g., `"Schaefer400"`). Consequently the verification command `load_atlas('Schaefer400')` would fail, and the required `data/atlas/` directory is missing. The task’s download, caching, extraction, and function‑signature requirements are not met.
- **T006** — Requested task execution failed; rerun successfully: code/src/data/quality_check.py exit=1
