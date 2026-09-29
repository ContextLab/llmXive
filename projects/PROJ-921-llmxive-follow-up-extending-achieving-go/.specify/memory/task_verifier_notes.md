# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory or its subfolders (`code/data`, `code/inference`, `code/scoring`, `code/analysis`, `code/utils`) is provided; the required directory structure is absent.
- **T001b** — No evidence was provided that the `data/` directory or its subfolders (`raw`, `processed`, `gold`) actually exist; the claim is unsubstantiated. The implementer must supply a file‑system listing, screenshot, or script output confirming the creation of these directories.
- **T001c** — No evidence was provided that a `tests/` directory (with `unit` and `integration` sub‑directories) actually exists in the repository; the implementer’s response contains only the task description and no file‑system listing or code showing the directories were created. The required directory structure is therefore missing.
- **T001f** — No `.gitignore` file was provided in the evidence, and therefore the required list of ignored patterns (`.pyc`, `__pycache__/`, `data/`, `*.log`, etc.) is missing. The task is not satisfied.
- **T009** — The required artifact `tests/unit/test_data_loader.py` does not exist on disk, so no contract test for the dataset loader is present. Without this file, the task’s deliverable is missing.
