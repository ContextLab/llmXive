# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — Checked `code/utils/config.py` – it correctly defines `SEEDS`, `PATHS`, and `SENSITIVITY_THRESHOLDS = [2,3,4]`.  
Checked `code/ingest/checksum.py` – while the functions now use a list‑of‑dict schema and `main()` exits non‑zero on failures, the script imports `from utils.config import …` which is an invalid import (the module lives at `code/utils/config.py`). This will raise `ModuleNotFoundError`, so the script cannot actually run the verification as claimed. The import must be fixed (e.g., `from code.utils.config import …`) for the task to be complete.
- **T102** — The `link_dataframe` function is present, but the fuzzy‑matching branch does not extract entities from the test sentences, causing the test `test_fuzzy_matching_threshold_behavior` to fail (expected “Apple” but got `None`). Consequently the unit‑test suite does not pass, so the task’s verification requirement is not met.
- **T103** — Requested task execution failed; rerun successfully: code/ingest/download_data.py exit=1
