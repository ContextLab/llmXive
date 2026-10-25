# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/dataset/generator.py` writes a JSONL file (one puzzle per line), but `code/tests/test_verifier.py` expects a single JSON object containing a `"puzzles"` list and reads it with `json.load`. This mismatch causes the verifier test to fail, so the required test suite does not pass. The generator’s output format must be changed to match the test’s expectations (or the test must be updated).
- **T003** — Requested task execution failed; rerun successfully: code/bes/main.py exit=1
