# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The `code/utils/logging.py` file exists and is non-empty, but it does not satisfy the task requirement to "handle logging of environmental parameters" in a way that supports the feature specification's mandatory User Story 1.

**Critical deficiencies:**

1. **No actual environmental parameter capture**: The module provides helper functions like `log_environmental_params()` and `log_compliance_check()`, but these are passive wrappers that accept pre-constructed dictionaries. There is no code that actually *measures* or *validates* environmental parameters (temperature, humidity, barometric pres
- **T006a** — The schema file exists and is non-empty, but it does **not match the task's stated requirements**. The task explicitly specifies that the schema must have these four fields: `name`, `dielectric_constant`, `source_id`, and `citation_url`. The artifact instead includes `version_hash` as a required field and omits `citation_url` entirely. While `version_hash` may be useful for reproducibility, it was not requested; conversely, `citation_url` — a field explicitly named in the task specification — is missing. The schema also uses `source_id` with a restrictive NIST-specific pattern (`^NIST-SRD-[0-9
- **T006b** — The `solvents.yaml` file exists and contains NIST dielectric constants, but it is missing two of the five explicitly required solvents. The task specifies "≥5 solvents (cyclohexane, toluene, acetonitrile, methanol, water)" as mandatory entries. The artifact provides cyclohexane, toluene, acetonitrile, ethanol, and dichloromethane—but **methanol and water are absent**. While the file contains 5 solvents total, it does not include the specific required solvents methanol and water that are named in the task specification. This is a substantive gap: the task explicitly lists these five solvents as
- **T006c** — The task requires validation of `solvents.yaml` against `solvent.schema.yaml`, but both files are MISSING from the project root. Without these two artifacts, no validation work could have been performed. The implementer cannot have completed schema validation when the files to be validated do not exist.

To complete this task, the implementer must create both `solvents.yaml` (containing solvent definitions with properties like dielectric constant, as referenced in User Story 1) and `solvent.schema.yaml` (the schema defining the structure and constraints), then demonstrate that validation passe
- **T017c** — declared artifact(s) missing/empty/invalid: code/analysis/hash_manager.py, solvents.yaml, state/artifact_hashes.yaml
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
