# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006c** — Both required artifacts (`solvents.yaml` and `solvent.schema.yaml`) are reported as MISSING, so no validation could be performed. The task’s core requirement—to validate the solvent list against its schema—is not met.
- **T008** — The `code/data/loaders.py` implementation is present, but the required `solvents.yaml` lookup table is missing, so the loader cannot actually read and validate any records. Without this file the functions will raise `SolventDataError`, failing the core requirement of reading and returning validated solvent records. Adding the `solvents.yaml` file (with the expected structure) is needed to complete the task.
- **T009a** — The provided `code/config.py` defines directory paths and CPU‑only environment settings, but it does **not** declare the required constants (e.g., default substrate mass and integration time set to `None`) nor any logic to load or override them from a `config.yaml` or CLI arguments. Additionally, the `config.yaml` file is missing entirely. These omissions mean the task’s core requirements are not met.
- **T017c** — Requested task execution failed; rerun successfully: state/artifact_hashes.yaml exit=-1
- **T015f** — declared artifact(s) missing/empty/invalid: code/data/capture.py, data/raw/kinetic_traces/
- **T017b** — declared artifact(s) missing/empty/invalid: code/analysis/compliance.py, data/processed/compliance_report.json
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/kinetic_metrics.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.csv
- **T059b** — Requested task execution failed; rerun successfully: code/run_power_analysis.py exit=1
- **T029a** — declared artifact(s) missing/empty/invalid: data/compute/dft_results.csv
- **T029d** — declared artifact(s) missing/empty/invalid: data/chemicals/phenyl_benzoate.smi
- **T029c** — declared artifact(s) missing/empty/invalid: data/compute/solvent_solvation.csv
- **T031b** — declared artifact(s) missing/empty/invalid: data/processed/vif_raw_scores.json
- **T030b** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.json
- **T034** — declared artifact(s) missing/empty/invalid: paper/figures/regression_plot.png
- **T045** — declared artifact(s) missing/empty/invalid: code/analysis/calibration_protocol.py, data/chemicals/calibration_standards.yaml, data/processed/calibration_certificates/
- **T039** — declared artifact(s) missing/empty/invalid: tests/integration/test_full_pipeline.py
