# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The ingest module, quickstart doc, and test file exist with correct logic, but the recorded test run (`code/.tasks/T001.code_tests...log`) shows 4 of 5 tests FAILED with `ImportError: pyarrow/fastparquet missing`, so the required verification (tests covering valid inputs, missing file, and missing outcome column all passing) is not satisfied. The implementer must add a parquet engine (e.g., `pyarrow`) to the project's pinned `requirements.txt` (or otherwise make the tests runnable in the platform environment) and re-run the tests to green; there is also no execution evidence of `python -m code
- **T002** — Requested task execution failed; rerun successfully: code/src/pipeline/preprocess.py exit=1
