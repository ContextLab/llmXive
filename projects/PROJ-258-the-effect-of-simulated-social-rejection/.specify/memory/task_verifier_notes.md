# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires three verifiable conditions: (1) all directories with `__init__.py` files exist, (2) `code/requirements.txt` contains exact pinned versions, and (3) `quickstart.md` exists with the full pipeline command AND `pip install -r code/requirements.txt` succeeds in a fresh virtual environment.

**Evidence checked:**
- ✓ All required directories (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `results/`, `paper/`, `tests/`) exist with `__init__.py` files (confirmed by directory listings).
- ✓ `code/requirements.txt` exists with pinned versions (pandas==2.2.2, numpy==1.26.4,
- **T002** — Requested task execution failed; rerun successfully: code/ingest.py exit=1
