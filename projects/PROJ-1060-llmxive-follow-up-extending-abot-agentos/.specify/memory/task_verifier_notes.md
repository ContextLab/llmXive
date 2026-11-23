# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — Requested task execution failed; rerun successfully: code/data_loader.py exit=1; code/data_loader.py exit=1
- **T008** — The `tests/conftest.py` file exists, but it does not define the required pytest configuration variables `pythonpath = ["code"]` and `addopts = "-v"`; it only adds a fixture that manipulates `sys.path`. The task explicitly asked for those settings to be present in the conftest file, so the implementation is incomplete.
- **T024** — declared artifact(s) missing/empty/invalid: tests/integration/test_gpu_free.py
- **T032** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
