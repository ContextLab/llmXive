# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `src/data/download.py` script and the downloaded files exist and follow the specification, but the required unit test `tests/unit/test_download.py` does **not** pass – it aborts with `ModuleNotFoundError: No module named 'requests_mock'`. The task explicitly requires the pytest suite to succeed, so the missing `requests_mock` dependency (or an alternative test setup) must be added for the verification to be satisfied.
- **T002** — Requested task execution failed; rerun successfully: src/data/preprocess.py exit=1
