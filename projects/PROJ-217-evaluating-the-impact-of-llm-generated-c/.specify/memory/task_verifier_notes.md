# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The script `src/utils/verify_requirements.py` exists and its content correctly implements existence, non-empty, and optional SHA-256 checks with a boolean return and exit code. However, the required log artifact `data/requirements_check.log` is MISSING, meaning there is no evidence the script was ever executed — the task explicitly requires it to log to that file, and the implementer's completion claim has no run evidence backing it. The implementer should run the script (e.g., `python -m src.utils.verify_requirements`) to produce the log and confirm it passes against the existing non-empty `r
- **T001** — Requested task execution failed; rerun successfully: scripts/run_tests.sh exit=1
- **T004** — Requested task execution failed; rerun successfully: src/utils/validate_environment.py exit=1
