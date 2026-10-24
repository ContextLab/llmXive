# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: src/data/generate_comments.py exit=1
- **T003** — The provided `src/data/metrics.py` writes the CSV and computes the required scores, but it loads the entire JSONL file into memory (no streaming) and, more critically, the test suite fails: `test_metrics_produce_expected_values` expects BLEU, ROUGE‑L and semantic similarity of 1.0 for the `*_vs_source` columns, yet the generated CSV contains `0.0` for those fields (the comment is not identical to the source code). Consequently the verification tests do not pass, and the streaming‑batch requirement is not satisfied.
- **T005** — Requested task execution failed; rerun successfully: scripts/run_smoke.py exit=1
