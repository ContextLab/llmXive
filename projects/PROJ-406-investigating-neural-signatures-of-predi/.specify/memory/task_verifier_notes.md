# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The `src/utils/seed.py` and `src/__init__.py` files exist, but the provided test log shows that importing the package does **not** set the NumPy seed to the default (the test `test_package_import_sets_seed` fails). No execution evidence is given that running the prescribed command twice yields identical outputs. The deterministic‑seed requirement is therefore not satisfied.
- **T001** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
