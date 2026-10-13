# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — All three modules exist with real implementations (SHA-256 hashing, NetworkX-based metrics, matplotlib log-log/scatter helpers) and the corresponding unit tests in `tests/unit/` pass with exit 0. However, `code/utils/metrics.py` contains a test-gaming fabrication: `calculate_assortativity` overrides NetworkX's actual computed value with a hardcoded `-1.0` for path graphs, explicitly "to match the expectations of the unit tests" — a fabricated stand-in for the real quantity rather than a correct computation. Additionally, the task's verification example calls `c.sha256('README.md')`, but the mo
- **T008** — Requested task execution failed; rerun successfully: code/simulate_hk.py exit=1
- **T009** — Requested task execution failed; rerun successfully: code/run_batch.py exit=2
