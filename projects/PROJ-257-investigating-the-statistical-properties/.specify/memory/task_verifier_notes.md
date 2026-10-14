# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `src/data/download.py` script exists but the unit test `tests/unit/test_download.py` cannot pass because it mocks a Zenodo record ID (123456) that does not match the DOIs hard‑coded in the script (3966973/3966974), so the mocked API calls are never used. Moreover, the required output files `data/raw/gwtc1.h5`, `data/raw/gwtc2.h5`, and `data/raw/checksums.json` are absent. The task’s verification conditions are therefore not met.
- **T002** — Requested task execution failed; rerun successfully: src/data/preprocess.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/main.py exit=1
