# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The generated `simulation_raw.json` contains only a handful of replicates (6 total) instead of ≥500 replicates for each heterogeneity level, and the required schema file `contracts/simulated_dataset.schema.yaml` is missing, so we cannot confirm output conforms to the contract. The implementation does not meet the quantity and validation requirements.
- **T012** — No evidence of a modified `generator.py` is provided; there is no code snippet, diff, or test output demonstrating handling of the τ² = 0 edge case, nor any indication that numerical instability was addressed. The required artifact is missing, so the task is not satisfied.
