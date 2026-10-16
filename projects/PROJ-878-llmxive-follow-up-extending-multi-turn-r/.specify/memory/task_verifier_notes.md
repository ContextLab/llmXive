# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/graph_generator.py exit=1
- **T002** — The test file `code/tests/test_graph_generator.py` exists, but the recorded test run shows both parametrized tests fail with an `AttributeError` because `networkx` has no `set_seed` function (line 23 in `graph_generator.py`). Consequently the schema‑conformance and orthogonalization checks never succeed, so the required contract and integration tests do not pass after T003. The generator code must be corrected (e.g., remove the invalid `nx.set_seed` call or use a proper RNG seed) and the tests re‑run to achieve a passing result.
- **T003** — Requested task execution failed; rerun successfully: code/graph_generator.py exit=2; code/graph_generator.py exit=2
