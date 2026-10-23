# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The unit test `tests/unit/test_data_loader.py` fails with a `FileNotFoundError` because it looks for the script at `tests/code/01_ingest_and_filter.py` instead of the actual location `code/01_ingest_and_filter.py`; consequently the test never reaches the intended `DataFetchError` assertion. This means the required verification that a simulated fetch failure raises `DataFetchError` is not satisfied. Fix the test’s path (or adjust the import logic) so it correctly loads the script and the test can pass.
