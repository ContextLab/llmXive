# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided `env_check.py` correctly imports the required packages, but `code/tests/test_env_check.py` runs it as `python -m src.env_check`, which looks for `src/env_check.py` that does not exist (the script is at `code/src/env_check.py`). Additionally, the test expects a `data/raw/checksums.json` file, which is not present in the repository. These mismatches cause the verification test to fail.
- **T001-1** — The `requirements.txt` is properly pinned and `data/raw/checksums.json` is an empty JSON object, but `quickstart.md` documents the command `python -m src.run_e2e` instead of the required `python -m code.src.run_e2e`. This deviation means the documentation does not meet the task specification.
- **T014** — Requested task execution failed; rerun successfully: code/src/acquire_external.py exit=1
