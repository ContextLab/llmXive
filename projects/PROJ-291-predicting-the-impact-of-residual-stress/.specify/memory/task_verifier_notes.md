# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository lacks a `src/env_check.py` module required by `test_env_check.py` (the test runs `python -m src.env_check`), and there is no evidence of the expected `data/raw/checksums.json` file that the test also checks. Consequently the pytest suite cannot pass, so the task’s requirements are not fully satisfied.
- **T001-1** — The `requirements.txt` is properly pinned and `data/raw/checksums.json` is an empty JSON object, but `quickstart.md` documents the command `python -m src.run_e2e` instead of the required `python -m code.src.run_e2e`. This deviation means the documentation does not meet the task specification.
- **T014** — Requested task execution failed; rerun successfully: code/src/acquire_external.py exit=1
