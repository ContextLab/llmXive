# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directory `data/raw/` is missing (marked MISSING), so the project layout is incomplete despite the presence of `logs/structure.txt` and the documented command in `quickstart.md`. The implementer must add the `data/raw/` directory to satisfy the task.
- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
- **T003** — The repository contains `src/data/validate_raw.py` and the unit‑test file, but the CLI cannot be invoked (`python -m src.data.validate_raw` raises “No module named src.data.validate_raw”) because `src` is not a package (no `src/__init__.py`). Consequently the tests fail, no log files are written, and the script does not use the `jsonschema` library as required. The task needs a proper package layout, correct importable module, use of `jsonschema` for schema loading/validation, and passing unit tests.
- **T004** — Requested task execution failed; rerun successfully: src/data/clean.py exit=1
