# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — The `code/data/schema_validator.py` file exists but its implementation is incomplete (truncated logic) and it depends on `contracts/dataset.schema.yaml`, which is missing from the repository, so the validator cannot actually validate against the required schema.
- **T017** — No `normalization_bounds.json` file was presented in the evidence, nor any description of its contents or location under `data/processed/`. Without the actual JSON artifact containing the train‑set min/max values, the task requirement is not satisfied.
- **T026** — No model files (e.g., `gpr_model.pkl` and `linear_regression.pkl` or similar) are present in the `results/models/` directory, nor any evidence (logs, screenshots, or code) showing that the trained GPR model and Linear Regression baseline were saved there. The required artifacts are missing.
- **T027** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T030** — declared artifact(s) missing/empty/invalid: results/baseline_correlation.json
