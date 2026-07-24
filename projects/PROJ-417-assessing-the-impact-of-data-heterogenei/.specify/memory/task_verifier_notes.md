# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T040** — declared artifact(s) missing/empty/invalid: data/raw/cochrane_base.csv
- **T040b** — The required `data/raw/cochrane_base_synthetic.csv` file does not exist, and there is no evidence that the script was run or that `research.md` was updated to document the synthetic fallback source. Consequently the task’s core deliverable is missing.
- **T010** — The repository contains a partially implemented `generator.py`, but it lacks a complete replication loop for the five τ² levels and does not produce any output files. Moreover, the required schema file `contracts/simulated_dataset.schema.yaml` is missing, so the output cannot be validated against the contract. The next implementer must add the full simulation loop (≥500 replicates per level), ensure the generated datasets include the `injected_true_effect` and `injected_tau2` columns, and provide the missing schema file.
- **T011** — No code artifact (e.g., modified `generator.py`) was provided to show the required logic for handling cases where the number of studies N is < 5. Without the actual implementation or a description of the changes, we cannot confirm that the edge‑case handling (flagging/excluding replicates) has been added. The task remains unfinished.
- **T012** — No `generator.py` file or code snippet was provided, and there is no evidence that any logic handling the τ² = 0 edge case was added. Without the actual implementation (or a description of the changes) we cannot confirm the required functionality exists. The next implementer must supply the updated `generator.py` showing the zero‑variance handling logic.
- **T013** — declared artifact(s) missing/empty/invalid: data/results/simulation_raw.json, schema.yaml
