# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The `src/utils/seed.py` correctly defines `set_global_seed(42)` and the manual‑seed test passes, but `src/__init__.py` fails to set the seed on import – the test `test_package_import_sets_seed` reports mismatched NumPy outputs (0.9507 vs 0.3745). Consequently the required deterministic behavior across imports is not achieved. The implementation must ensure that importing `src` pins the global seed as specified.
- **T001** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
