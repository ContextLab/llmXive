# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/verify_scaffolding.py exit=1
- **T002** — The required test run fails: the recorded execution log shows `pytest code/tests/unit/test_generator.py` exits 1 with 2 failures — `test_skewness_within_01_of_target[2.0]` (sample skewness 1.89, off by 0.11 > 0.1 tolerance) and `test_from_config` (test passes `mean=` but `SimulationConfig` has no `mean` field, only `mean_diff`). The generator and test files exist and are substantive, but the verification requirement "pytest passes" is not met; fix the skewness realization for target 2.0 (e.g., larger n, moment matching, or different skewed distribution) and correct the `SimulationConfig` field
