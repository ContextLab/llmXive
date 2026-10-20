# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains the required schema files, `requirements.txt`, `seeds.py`, and a detailed `quickstart.md`, but there is no evidence that `pytest tests/contract/` actually runs and passes. Without test execution logs or a passing test report, the verification condition is unmet. Provide the pytest run output (or a CI badge) showing all contract tests succeed.
- **T002** — Requested task execution failed; rerun successfully: code/verify_dataset.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/data/loader.py exit=1
- **T004** — The `src/graphs/composition.py` file exists and implements most of the required logic, but the unit‑test suite cannot be run because the `pymatgen` package is not available, causing an import error. Moreover, the test that checks for an unknown‑element warning expects the warning message to contain “Unknown element”, which the current implementation does not emit (it logs a different message when parsing fails). Consequently the verification tests do not pass.
- **T005** — The unit test `test_generate_cv_folds_is_stratified_and_reproducible` fails (folds are not perfectly balanced, 6 vs 7 cubic/hexagonal entries), and the required output directory `data/processed/splits/` with the JSON split files does not exist. The implementation therefore does not meet the stratified‑CV and export requirements.
