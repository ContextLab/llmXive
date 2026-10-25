# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/tests/test_verifier.py` fixture reads the generator output with `json.load` and expects a JSON object containing a `"puzzles"` list, but `code/dataset/generator.py` writes a JSONL file (one JSON object per line). This mismatch causes a JSON decoding error, so the verifier tests cannot run and the required timing log is never written. The generator’s output format must be adjusted (or the test changed) to produce a single JSON object with a `"puzzles"` array for the verifier tests to pass.
- **T003** — Requested task execution failed; rerun successfully: code/bes/main.py exit=1
