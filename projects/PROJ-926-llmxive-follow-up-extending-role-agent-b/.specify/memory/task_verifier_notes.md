# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T046** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py, data/raw/model_verification_log.json
- **T049** — The provided `src/sim/validation.py` does not contain any code that detects ambiguous failure trajectories, marks them as `EXCLUDED`, or writes entries with an `ambiguity_reason` to `data/raw/excluded_log.json`. Moreover, the required `data/raw/excluded_log.json` file is absent from the repository. These missing components mean the task’s specification is not satisfied.
- **T011** — The required `src/sim/trajectory_generator.py` file does not exist, the schema file `specs/001-llmxive-followup/contracts/trajectory_schema.yaml` is missing, and the test file lacks the promised `test_trajectory_schema_matches_spec` function (the file is truncated and does not implement the contract check).
- **T013** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py, data/raw/ground_truth_raw.json, data/raw/excluded_log.json, data/raw/generation_log.json, data/raw/baseline_failures.json
