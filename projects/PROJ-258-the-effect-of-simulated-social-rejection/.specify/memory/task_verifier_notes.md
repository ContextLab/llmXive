# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directory tree is present but `data/raw/` and `data/processed/` lack the required placeholder `__init__.py` files, and there is no provided evidence that `python -c "import pandas"` was executed successfully. These omissions mean the task’s specifications are not fully satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/ingest.py exit=2
- **T003** — The verification shows that neither `data/raw/ds003392.parquet` nor the fallback `data/interim/reward_unavailable.json` exist, and the provided ingestion test fails (missing parquet engine and SystemExit). Consequently the required download or recorded unavailability artifact is absent, so the task is not satisfied.
- **T004** — Requested task execution failed; rerun successfully: code/validate.py exit=1
