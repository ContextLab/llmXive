# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the `projects/PROJ-413-predicting-molecular-interactions-in-pol/` directory or its subfolders (`data/raw`, `data/curated`, `data/processed`, `code/data`, `code/models`, `code/analysis`, `code/utils`, `results`, `analysis`, `docs`, `tests/contract`, `tests/integration`) is provided. The required directory tree must be created and shown (e.g., via a directory listing) to satisfy the task.
- **T001b** — No evidence of a Git repository being initialized in the specified path nor a `.gitignore` file for Python is present; the required artifacts are missing.
- **T005** — The `code/utils/logger.py` defines a `PerformanceLogger` but the snippet is truncated before the `_save` method that actually writes to `results/performance.json`, and the `results/performance.json` file is missing entirely. Without a functioning save routine and the required output file, the logging infrastructure is not fully set up.
- **T063** — No `spec.md` file or its contents were provided, so we cannot confirm that FR-003 now states “3-layer Graph Attention Network (GAT)” and that FR-007 has been clarified as required. The necessary artifact is missing.
