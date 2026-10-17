# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: code/data/fetch_ace.py exit=2; code/data/fetch_noaa.py exit=2
- **T003** — The required test `code/tests/test_sync.py` is MISSING, so the mandated verification (`pytest code/tests/test_sync.py::test_sync_monthly`) cannot pass. The output `data/processed/synced.csv` contains only 24 rows covering a single day (2003-10-01) of obviously synthetic, perfectly-linear fixture data (no real ACE/NOAA raw data exists in `data/raw/`), not a representative month of real data; the fixture fallback fabricates the "real data" requirement. Additionally, no interpolated rows exist (all `interpolated_flag=False`), so the gap-interpolation behavior is untested/undemonstrated, and the s
- **T006** — Requested task execution failed; rerun successfully: code/viz/plots.py exit=1
