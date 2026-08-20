# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008c** — The repository contains a partially‑written `generate_tdp_constant.py` that is truncated (the `save_calibrated_tdp` function is incomplete) and no code actually writes `data/processed/calibrated_tdp.json`. Moreover, the required input file `data/processed/calibration_run.json` is absent, so the script cannot be executed to produce the specified output. The task’s core requirements are therefore unmet.
- **T036** — The required input file `data/processed/distribution_validation.json` is missing, so the validation could not actually be performed; the existing `validation_gate.json` cannot be trusted as genuine evidence of a completed check. The task therefore fails to meet its core requirement.
- **T019d** — The provided `exclusion_logger.py` is truncated (ends with a syntax error) and does not guarantee writing to the required `data/processed/exclusions.json` path. The referenced schema file (`contracts/output.schema.yaml`) is missing, so adherence cannot be verified, and the expected JSON output file does not exist.
- **T040b** — declared artifact(s) missing/empty/invalid: data/processed/literature_gpu_factor.json
- **T040c** — The required `data/processed/literature_gpu_factor.json` file is absent, and the provided `code/analysis/metrics.py` does not contain any implemented logic that reads this file and checks that the conversion factor is non‑zero (the file is truncated before any such function). Both the artifact and the validation step are missing.
- **T029g** — declared artifact(s) missing/empty/invalid: data/processed/scaling_raw_logs.json, data/processed/neural_baseline_logs.json
- **T035** — The required artifact `pre_registration.yaml` is missing from the provided evidence, so the set of required files is not complete, violating the verification constraint.
- **T035#1** — The required artifact `pre_registration.yaml` is missing from the repository, so the set of required files is incomplete and the verification task is not satisfied.
