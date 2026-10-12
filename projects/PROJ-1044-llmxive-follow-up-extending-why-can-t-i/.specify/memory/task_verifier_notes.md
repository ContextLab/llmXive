# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `src/data/something_loader.py` cannot load the required dataset (both identifier attempts raise `DatasetNotFoundError`), causing the unit test `tests/test_something_loader.py` to fail during execution. Consequently the loader does not successfully yield any video bytes/labels, and the test does not pass. The task needs a working dataset load (or a mock/fake dataset for testing) and a passing unit test.
- **T003** — Requested task execution failed; rerun successfully: src/data/counterfactual.py exit=1
