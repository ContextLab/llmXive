# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T102** — The `link_dataframe` implementation does not correctly perform the fuzzy‑matching branch: it passes the whole question string to `EntityLinker.link_entity`, which fails to match “I love apples” to the node “Apple”, causing the `test_fuzzy_matching_threshold_behavior` unit test to fail. Consequently the required behavior and the passing test suite are not satisfied.
- **T103** — Requested task execution failed; rerun successfully: code/ingest/download_data.py exit=1
