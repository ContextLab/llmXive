# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required top‑level directory `specs/PROJ-924/` does not exist (marked MISSING), so the project structure is incomplete despite the test and log being present. The task also expects this specs folder to be created under the repository root.
- **T002** — The provided `requirements.txt` omits the required `scipy` package and `pyproject.toml` does not list any of the mandated dependencies. Moreover, the expected `data/processed/pytest_manifest_log.txt` file is missing, so the pytest run and its “1 passed” logs cannot be verified. These gaps must be fixed for the task to be complete.
- **T010d** — Requested task execution failed; rerun successfully: code/run_lint_test.py exit=5
