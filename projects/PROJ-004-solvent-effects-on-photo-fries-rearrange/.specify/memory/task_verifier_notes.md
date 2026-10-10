# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006c** — The task requires validation of `solvents.yaml` against `solvent.schema.yaml`, but both files are MISSING from the project root. Without these two artifacts, no validation can occur. The implementer cannot have completed schema validation when the files to be validated do not exist on disk.
- **T007** — The artifact `contracts/kinetic_trace.schema.yaml` exists and is non-empty, but it does not satisfy the task's requirement as stated in the feature specification.

**Critical deficiency**: The task requires a schema that validates **kinetic trace data** in the context of the three user stories, particularly User Story 1 (solvent series configuration with environmental logging) and User Story 2 (radical-pair lifetime extraction). The schema provided defines the structure for individual trace records but **lacks the contract definitions necessary to support the experimental workflow**:

1. **Mis
- **T017c** — Requested task execution failed; rerun successfully: state/artifact_hashes.yaml exit=-1
- **T015f** — declared artifact(s) missing/empty/invalid: code/data/capture.py, data/raw/kinetic_traces/
- **T017b** — declared artifact(s) missing/empty/invalid: code/analysis/compliance.py, data/processed/compliance_report.json
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/kinetic_metrics.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.csv
- **T059b** — declared artifact(s) missing/empty/invalid: data/processed/study_power_analysis.json
- **T029a** — declared artifact(s) missing/empty/invalid: data/compute/dft_results.csv
- **T029d** — declared artifact(s) missing/empty/invalid: data/chemicals/phenyl_benzoate.smi
- **T029c** — declared artifact(s) missing/empty/invalid: data/compute/solvent_solvation.csv
- **T031b** — declared artifact(s) missing/empty/invalid: data/processed/vif_raw_scores.json
- **T030b** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.json
- **T034** — declared artifact(s) missing/empty/invalid: paper/figures/regression_plot.png
- **T045** — declared artifact(s) missing/empty/invalid: code/analysis/calibration_protocol.py, data/chemicals/calibration_standards.yaml, data/processed/calibration_certificates/
- **T039** — declared artifact(s) missing/empty/invalid: tests/integration/test_full_pipeline.py
