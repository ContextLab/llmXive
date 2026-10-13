# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Checked `code/utils/metrics.py` and its unit tests (`tests/unit/test_metrics.py`), which both fail (assortativity returns –0.333 instead of –1.0 and returns NaN for regular graphs, causing assertions to fail). The other modules (`checksums.py`, `plotting.py`) exist and pass their tests. The core metrics utilities therefore do not meet the task requirements.
- **T005** — Requested task execution failed; rerun successfully: code/generate_networks.py exit=1
