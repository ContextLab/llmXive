# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/data/acquire_real.py exit=1; code/data/download_real.py exit=1
- **T002** — The repository contains the generator script, the synthetic `.py` files, the manifest CSV and the cap‑warning log, all of which appear correct, but there is no concrete evidence that the command `python -m src.data.generate_synthetic --seed 42` was actually executed and exited with status 0, nor any proof that the manifest CSV contains exactly 200 rows (the row count is not shown). Provide a recorded run (e.g., command‑line output or a test script asserting exit code 0 and row count 200) to satisfy the verification criteria.
- **T004** — Requested task execution failed; rerun successfully: src/features/extract.py exit=1
