# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml, black.toml
- **T009** — The provided `code/src/data/preprocessing.py` contains only a partial `stream_batch` implementation (it never yields batches or enforces the 50‑example limit) and does not include any `datasets.load_dataset` handling that raises `ConnectionError`/`FileNotFoundError`. Moreover, the integration test `tests/integration/test_preprocessing.py` checks `stream_tokens_in_batches` and other utilities but never verifies the required `stream_batch` 50‑token batching behavior. Consequently, the core function and its verification are missing.
- **T010** — The provided `download.py` only implements streaming download and 500‑example capping for GSM8K; there is no analogous logic for the MiniGrid dataset, and the file is located at `code/src/data/download.py` rather than the required `projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/data/download.py`. Both the missing MiniGrid implementation and the incorrect file location prevent the task from being satisfied.
- **T012a** — declared artifact(s) missing/empty/invalid: data/canonical_ground_truth.jsonl
