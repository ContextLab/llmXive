# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/requirements.txt` file exists and includes all required packages, but none are version‑pinned as the task specifies “pinned dependencies,” and there is no evidence (e.g., pip install logs) showing that `pip install -r code/requirements.txt` completes without conflicts. Adding explicit version specifiers and providing successful install verification are needed.
- **T003** — The repository contains a `code/pyproject.toml` with proper Ruff and Black configuration, but there is no execution evidence (logs, exit codes, or output) showing that `ruff .` and `black .` were run and completed without errors or formatting changes. Without such proof, the task’s verification requirement is not satisfied.
- **T009a** — declared artifact(s) missing/empty/invalid: data/raw/mp_raw.json
- **T009b** — declared artifact(s) missing/empty/invalid: data/raw/nist_alloys.json
- **T009c** — Requested task execution failed; rerun successfully: code/data/merge_sources.py exit=1
