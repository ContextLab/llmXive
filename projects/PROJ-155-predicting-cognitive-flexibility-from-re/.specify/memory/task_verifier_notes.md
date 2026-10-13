# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories, `requirements.txt`, `.ruff.toml`, and `code/config.py` all exist with correct content, but the core verification requirement fails: `data/logs/ruff.log` (735KB) is full of lint errors (E501, F401, I001, UP035, W291, etc. across `code/analysis/fdr_correction.py` and other files) and does not contain "✔ No errors". The implementer must fix the lint violations (or adjust the config appropriately) and re-run `ruff check . > data/logs/ruff.log` until the log reports no errors.
- **T002** — Requested task execution failed; rerun successfully: code/main.py exit=-1 (TIMEOUT)
