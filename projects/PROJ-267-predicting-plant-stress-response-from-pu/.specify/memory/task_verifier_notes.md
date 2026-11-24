# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The `code/utils/constants.py` file exists and defines `SEED` with calls to `np.random.seed` and `random.seed`, but the provided test (`tests/test_constants.py`) fails during import due to a circular‑import error in the `code.utils` package, so the seed‑pinning behavior is never exercised. Moreover, there is no evidence that other stochastic modules import and use this constant, nor is a scikit‑learn seed explicitly set. The task’s verification requirements are therefore not met.
- **T003** — Requested task execution failed; rerun successfully: code/utils/verify_logging_imports.py exit=1
- **T002** — Requested task execution failed; rerun successfully: code/data/ingest.py exit=1
