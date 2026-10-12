# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `src/data/something_loader.py` implements a streaming loader with a seed, but the unit test `tests/test_something_loader.py` fails at runtime because the HuggingFace dataset `"something-something-v2"` cannot be loaded, and the test only checks URL strings—not that video frames are non‑empty as required. The task therefore lacks a passing test that validates actual video content.
- **T003** — Requested task execution failed; rerun successfully: src/data/counterfactual.py exit=1
