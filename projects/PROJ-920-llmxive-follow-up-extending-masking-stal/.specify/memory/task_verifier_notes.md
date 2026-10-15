# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The current `tests/unit/test_density_isolation.py` (627 bytes, single function `test_composite_density_isolated`) does not match the execution log, which claims 10 tests in a `TestDensityIsolation` class (e.g., `test_density_independent_of_agent_output`, `test_no_global_state_dependency`) — so the recorded run corresponds to a different, since-replaced version of the file, and there is no evidence the current test was ever executed. Additionally, the current test only checks the 0.6/0.4 composite formula; it does not verify independence from agent-output data as the task requires. The implemen
- **T011** — Requested task execution failed; rerun successfully: code/validate_trajectories.py exit=1
- **T012** — Requested task execution failed; rerun successfully: code/validate_trajectories.py exit=1
