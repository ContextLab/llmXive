# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains `code/bootstrap.py` and a `code/requirements.txt`, but there is no evidence that the bootstrap script was actually executed successfully (no run log, no proof that it created the directories or wrote the pinned requirements). Moreover, the provided test for the script fails because it cannot monkey‑patch `paths.root`, indicating the script is not currently runnable in the expected environment. A successful execution record (or passing test) and confirmation that the generated `requirements.txt` matches the pinned list are needed.
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
