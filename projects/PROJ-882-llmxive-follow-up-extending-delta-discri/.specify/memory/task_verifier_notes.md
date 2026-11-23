# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015a** — declared artifact(s) missing/empty/invalid: data/processed/delta_coefficients.json, schema.yaml
- **T015b** — The required files `data/processed/delta_coefficients.json` and `contracts/delta_oracle.schema.yaml` are missing, so no validation could have been performed. The task’s core requirement is not satisfied.
- **T015c** — No code, script, or test output was provided that actually computes the global variance of the DelTA coefficients, checks it against the 1e‑9 threshold, or raises `RuntimeError('ERR_TRIVIAL_TARGET')` on failure. The required artifact is missing, so the task is not satisfied.
- **T015d** — The required artifact `data/processed/delta_coefficients.json` does not exist, so there is no data to inspect for NaN or Inf values. The task cannot be verified until the file is present and contains valid numeric entries.
