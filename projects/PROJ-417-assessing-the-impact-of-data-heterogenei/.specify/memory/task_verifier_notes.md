# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The repository lacks the required `contracts/simulated_dataset.schema.yaml` file, so the generator cannot be verified to produce schema‑conforming output. Moreover, the provided `generator.py` is incomplete (truncated) and does not show a loop that creates ≥500 replicates for each heterogeneity level nor writes results with the required `injected_true_effect` and `injected_tau2` columns. Both the schema and full implementation are missing.
- **T012** — No `generator.py` file or code snippet was provided, and there is no evidence that any logic handling the τ² = 0 edge case was added. Without the actual implementation (or a description of the changes) we cannot confirm the required functionality exists. The next implementer must supply the updated `generator.py` showing the zero‑variance handling logic.
