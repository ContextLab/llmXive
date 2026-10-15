# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The test file exists and is non-empty, but its tests contradict the actual implementation they're supposed to test: `calculate_composite_density` in `code/utils/heuristics.py` takes `(text, terms)` and applies fixed 0.6/0.4 weights, while the tests call it as `calculate_composite_density(entropy_val, tech_ratio, alpha, beta)` with arbitrary weights — every composite-density test would fail with a TypeError or wrong result. Additionally, `test_all_technical_terms` expects ratio 1.0 for "search_context retrieval_window", but the implementation's regex tokenizer splits underscores, yielding token
- **T015** — Requested task execution failed; rerun successfully: code/validate_simulation.py exit=-1 (TIMEOUT)
