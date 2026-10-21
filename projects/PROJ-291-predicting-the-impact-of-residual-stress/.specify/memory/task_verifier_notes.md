# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `quickstart.md`, `code/src/env_check.py`, `code/src/config.py`, `requirements.txt`, `data/raw/checksums.json` and the presence of `code/tests/test_env_check.py`. The quickstart uses bash scripts instead of the required single‑command example, the `requirements.txt` pins `torch==2.3.0` without the `+cpu` suffix, and the verification test file `code/tests/test_env_check.py` is missing, so the required pytest check cannot be run.
- **T002** — The required implementation file `code/src/ingest.py`, the JSON fixture `code/tests/fixtures/openml_style_nested.json`, the test suite `code/tests/test_ingest.py`, and the generated outputs `data/processed/missing_flags.json` and `data/processed/unified_fatigue.csv` are all reported as missing, so the ingestion pipeline cannot be verified or executed.
- **T003** — Requested task execution failed; rerun successfully: code/src/run_e2e.py exit=1
