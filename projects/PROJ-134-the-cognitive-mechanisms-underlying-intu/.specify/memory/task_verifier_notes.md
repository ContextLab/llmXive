# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T051** — declared artifact(s) missing/empty/invalid: code/utils/schemas.py
- **T013** — The `code/data/simulation_mfq.py` script exists, but it does not read the required MDES value from `state/mdes_report.yaml`; instead it uses a hard‑coded `GROUND_TRUTH_EFFECT` and calls `validate_ground_truth_effect` without evidence that the function accesses the missing YAML file. Moreover, the `state/mdes_report.yaml` file itself is absent, so the required validation step cannot be performed. The task’s core requirement is therefore unmet.
