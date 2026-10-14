# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/bootstrap.py` script creates the directories and writes a `requirements.txt`, and `code/main.py` provides a CLI entry point, but the automated test `tests/test_bootstrap.py` fails (cannot monkey‑patch `paths.root` and thus does not verify the layout creation). This failure shows the bootstrap script does not meet the required behavior for establishing the project layout in a configurable location, so the task is not fully satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
