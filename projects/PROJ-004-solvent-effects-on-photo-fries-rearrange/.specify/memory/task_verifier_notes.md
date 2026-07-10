# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009 Implement `code/config.py` to enforce CPU-only execution constraints and define file paths for `data/raw/`, `data/compute/`, `data/processed/`** — The provided `code/config.py` defines the required data directory paths and a helper to create them, but it contains no logic that enforces CPU‑only execution (e.g., disabling GPU devices or raising errors when a GPU is detected). The task explicitly required such a constraint, so the implementation is incomplete.
- **T010 [P] Create `tests/unit/test_loaders.py` to verify solvent property loading against versioned lookup table** — No `tests/unit/test_loaders.py` file was provided or referenced in the evidence, so the required unit test verifying solvent property loading against the versioned lookup table is missing. The task remains undone.
