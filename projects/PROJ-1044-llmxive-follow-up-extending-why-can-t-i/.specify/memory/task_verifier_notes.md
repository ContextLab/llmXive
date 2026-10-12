# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `something_loader.py` raises a `RuntimeError` when the HuggingFace dataset cannot be accessed, and this exception propagates out of `something_stream`, causing the unit test `tests/test_something_loader.py` to fail (no items are yielded). The test therefore does not load five videos with decodable frames as required. The loader must handle the missing dataset gracefully (e.g., by using the fallback video) so that the test passes.
- **T003** — Requested task execution failed; rerun successfully: src/data/counterfactual.py exit=1
