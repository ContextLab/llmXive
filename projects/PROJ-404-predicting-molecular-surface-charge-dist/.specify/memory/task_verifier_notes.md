# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `tests/test_structure.py` test failed because it tries to run `projects/code/setup_structure.py`, which does not exist (the script is at `projects/PROJ-404-predicting-molecular-surface-charge-dist/code/setup_structure.py`). Consequently the verification step that should confirm all required directories and `__init__.py` files is not passing. The project must either place the `setup_structure.py` script at the expected path or adjust the test, and provide concrete evidence (e.g., file listings) that each `code/` subdirectory (`data`, `models`, `utils`) actually contains an `__init__.py`.
- **T004a** — The provided `code/utils.py` (955 bytes) contains utility functions but does not define the required module‑level constants `EXIT_CODE_BASELINE_LOSS = 2`, `EXIT_CODE_THRESHOLD_FAIL = 3`, and `EXIT_CODE_SUCCESS = 0`. Adding these constants to the file is needed to satisfy the task.
- **T056a** — Requested task execution failed; rerun successfully: code/data/loader.py exit=1
