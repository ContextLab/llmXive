# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The required files (`code/utils/config.py`, `logger.py`, `stats_aggregator.py`, `__init__.py`) exist, but no evidence shows their contents are substantive (no source shown), and the only execution record — `tests/test_utils_infrastructure.py` — failed with exit code 4 due to `NameError: name 'pytest' is not defined` in `tests/conftest.py` (missing `import pytest`), so the infrastructure has never been demonstrated to pass its tests. Fix the conftest import bug, re-run the test suite to a passing state, and ensure the utils modules contain real configuration/logging logic rather than placeholde
- **T017** — Requested task execution failed; rerun successfully: code/drift_analysis.py exit=1
- **T025** — Requested task execution failed; rerun successfully: code/main.py exit=-1 (TIMEOUT)
- **T026b** — declared artifact(s) missing/empty/invalid: outputs/global_stats.json
