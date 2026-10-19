# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The test suite passes, but the original utility scripts (`code/run_lint.py`, `code/run_quickstart_validation.py`) remain as stub files instead of being removed after migration, and there is no evidence that `.gitignore` was updated to exclude `t*.py` and temporary files. Both the required file deletions and the `.gitignore` change are missing.
- **T003** — The `sample_size_justification.md` file exists but contains 172 words, exceeding the 150‑word limit, causing the unit test `test_word_count_within_limit` to fail. Reduce the justification to ≤150 words.
- **T005** — Requested task execution failed; rerun successfully: code/data_loader.py exit=1
