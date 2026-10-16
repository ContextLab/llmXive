# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The repository contains the required `src/utils/seed.py` and `src/__init__.py` with a `set_global_seed` implementation, but there is no evidence (e.g., command‑line output logs) showing that running the prescribed Python command twice yields identical NumPy random values. Without this execution proof, the deterministic‑seed verification requirement is not satisfied.
- **T001** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
- **T002** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1; src/ingest/load_illusions.py exit=1
