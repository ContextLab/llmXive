# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — **Evidence checked:**

1. **Directory structure**: `code/src/` exists with `__init__.py`, `config.py`, and `main.py`, but the required subdirectories `data/`, `analysis/`, `validation/`, and `utils/` are **missing**. The collector explicitly reports `data/: MISSING` and the directory listing shows only `__pycache__/`, `config.py`, `main.py`, and a `data/` entry that is not a directory (likely a file or symlink, not the required module).

2. **`code/tests/` structure**: Exists with `__init__.py` and test files, but the task requires it to be established as part of the skeleton—this is present.
- **T002** — Requested task execution failed; rerun successfully: code/src/data/loader.py exit=1
