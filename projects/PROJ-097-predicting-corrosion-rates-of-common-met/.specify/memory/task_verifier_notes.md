# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The provided `src/requirements.txt` uses wildcard version specifiers (e.g., `numpy==2.0.*`) instead of exact pinned versions, and `code/requirements.txt` contains different versions, extra packages, and is not byte‑identical to `src/requirements.txt`. No evidence of successful `pip install -r …` runs is supplied. The task’s requirement for exact, identical requirement files is therefore unmet.
- **T015** — The `quickstart.md` file exists but documents `python -m src.run_all` instead of the required `python -m src.pipeline.run_all`; therefore it does not contain the exact command the task mandates. The pytest command is present, but the missing/incorrect pipeline command makes the task incomplete.
- **T001** — Requested task execution failed; rerun successfully: code/run_ingest.sh exit=1; code/run_pipeline.sh exit=1
