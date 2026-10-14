# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T102** — The unit‑test suite does not pass: `tests/unit/test_entity_linker.py::test_fuzzy_matching_threshold_behavior` fails because `link_dataframe` feeds the full question string to the fuzzy matcher, so “I love apples” does not match the node “Apple”. The function needs to extract or otherwise isolate entity terms before fuzzy matching (or adjust similarity logic) to satisfy the fuzzy‑matching branch. Consequently the required verification (`pytest …` passes) is not met.
- **T103** — Requested task execution failed; rerun successfully: code/ingest/download_data.py exit=1
