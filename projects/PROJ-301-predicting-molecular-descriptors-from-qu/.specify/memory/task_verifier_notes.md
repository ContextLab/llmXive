# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T049** — The repository lacks `code/05_analysis.py`, so the failure boundary logic cannot be exercised. Moreover, the provided `tests/test_analysis.py` does not contain a test that explicitly asserts the AND condition (REI ≥ 10% **and** p < 0.0167) for the failure boundary logic. A proper unit test and the corresponding analysis module are needed.
- **T051** — No code, test logs, or output files were provided showing that `utils/memory_monitor.py` was exercised with a mocked `tracemalloc` returning > 6.5 GB, nor any evidence that the sampling loop backtracked and reduced the subset size. The required artifact (a demonstration of the fallback behavior) is missing.
