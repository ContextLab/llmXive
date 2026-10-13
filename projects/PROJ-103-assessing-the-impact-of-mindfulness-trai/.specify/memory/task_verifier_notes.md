# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked the directory tree (all required folders exist with `__init__.py`), the `settings.py` definitions (all required keys with type hints are present), and the `seeding.py` wrapper (which correctly re‑exports a module that pins NumPy, Python `random`, and optional PyTorch seeds). However, no unit‑test file is provided to demonstrate deterministic output on two runs of a trivial NumPy operation, so the test requirement is unmet. Adding the missing test (e.g., `tests/unit/test_seeding.py`) will be needed to complete the task.
