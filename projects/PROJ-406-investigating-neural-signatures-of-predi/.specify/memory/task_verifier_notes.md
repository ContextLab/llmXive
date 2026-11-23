# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The source files `src/utils/seed.py` and `src/__init__.py` exist and correctly implement `set_global_seed(42)` with package-import seeding, but the required verification artifact `outputs/seed_verification.log` is MISSING — the task explicitly requires running the seed-print command twice and capturing the two identical output lines in that log, and there is no execution evidence of reproducibility at all. The implementer must run the verification command twice, append both outputs to `outputs/seed_verification.log`, and confirm the two lines are identical.
- **T001** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
- **T002** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/ingest/clean_illusions.py exit=1
