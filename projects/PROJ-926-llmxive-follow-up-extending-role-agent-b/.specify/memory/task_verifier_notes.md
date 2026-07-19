# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T046** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py
- **T049** — The provided `src/sim/validation.py` does not contain any code that detects ambiguous failure trajectories, marks them as `EXCLUDED`, or writes entries with an `ambiguity_reason` to `data/raw/excluded_log.json`. Moreover, the required `data/raw/excluded_log.json` file is absent from the repository. These missing components mean the task’s specification is not satisfied.
- **T011** — The provided `tests/contract/test_trajectory_schema.py` is truncated (ends with “class Te”) and does not contain a complete test implementation, and the required module `src/sim/trajectory_generator.py` is missing entirely, so the contract test cannot be executed or validate the schema.
- **T013** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py, data/raw/ground_truth_raw.json
- **T013b** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py
