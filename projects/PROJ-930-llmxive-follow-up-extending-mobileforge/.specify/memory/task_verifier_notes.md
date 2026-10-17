# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires specific subdirectories, but the evidence shows they are missing: `code/` contains no `models/` directory, `code/data/` shows only `processed/` (no `raw/` or `evaluation/`), and `code/tests/` shows no `unit/` or `integration/` subdirectories. The implementer created many unrelated setup scripts (setup_dirs.py, create_directory_tree.py, etc.) but the actual required directory tree is not present.
- **T008** — Requested task execution failed; rerun successfully: code/data/raw/download_mobileforge.py exit=1
- **T009** — Requested task execution failed; rerun successfully: code/data/raw/validate_extraction_dataset.py exit=1
