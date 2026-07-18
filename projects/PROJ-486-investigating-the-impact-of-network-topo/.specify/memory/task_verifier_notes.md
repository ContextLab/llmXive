# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No directory listing or file system evidence was provided showing that the required subdirectories (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/visualizations/`, `tests/`, `tests/unit/`, `tests/integration/`, `docs/`) actually exist; without such artifacts the task cannot be considered completed.
- **T001c** — No evidence of any `.gitkeep` files was provided; the claim lacks the required artifact showing that every empty directory now contains a `.gitkeep` placeholder. The implementer must add and commit those files in all empty folders.
- **T012a** — The `load_entrainment_csv` function in `code/data_loader.py` is cut off mid‑implementation (the file ends with an incomplete return statement), so it never reaches the logic required to check for file existence, perform column validation, or return the mandated `{"exists": false, "reason": "missing"}` object. The missing implementation must be completed for the task to be satisfied.
