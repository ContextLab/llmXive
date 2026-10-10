# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006c** — Requested task execution failed; rerun successfully: code/validation/validate_solvents.py exit=1
- **T008** — The `code/data/loaders.py` implementation is present, but the required `solvents.yaml` lookup table is missing, so the loader cannot actually read and validate any records. Without this file the functions will raise `SolventDataError`, failing the core requirement of reading and returning validated solvent records. Adding the `solvents.yaml` file (with the expected structure) is needed to complete the task.
- **T009a** — The provided `code/config.py` defines directory paths and CPU‑only environment settings, but it does **not** declare the required constants (e.g., default substrate mass and integration time set to `None`) nor any logic to load or override them from a `config.yaml` or CLI arguments. Additionally, the `config.yaml` file is missing entirely. These omissions mean the task’s core requirements are not met.
- **T009b** — The provided `code/config.py` file exists (2829 bytes) but does not define an `EXPLICIT_SOLVENTS` list as required by task T009b. Adding a variable such as `EXPLICIT_SOLVENTS = ['water', 'methanol']` (or any appropriate list) is needed to satisfy the requirement.
- **T017c** — Requested task execution failed; rerun successfully: state/artifact_hashes.yaml exit=-1
- **T014** — The repository contains the `code/analysis/environment.py` module that can write logs, but the required output file `data/processed/environment_logs.json` is missing and no execution evidence is provided to show that the script has been run and produced the log. The task’s core deliverable – the actual environment log file – is absent.
- **T015e** — The required file `code/data/instrument_interface.py` is missing, so the `capture_transient_data()` API cannot be verified to exist or to raise `NotImplementedError` as specified. The task’s core deliverable is absent.
- **T015b** — The provided `code/data/ingest.py` aborts when `USE_REAL_DATA=True` and the file is missing, but it does **not** read the data path from a `config.py` setting (it uses an environment variable) and it only handles CSV files, not JSON as required. These deviations mean the task’s specification is not fully satisfied.
- **T015c** — The `generate_synthetic.py` script exists but it neither accepts a seed argument nor has been shown to actually produce the required `data/raw/synthetic_traces.csv` file (the file is missing). Consequently the task’s core requirement—deterministic synthetic trace generation with a seed and output path—is not met.
- **T015f** — declared artifact(s) missing/empty/invalid: code/data/capture.py, data/raw/kinetic_traces/
- **T016** — The repository contains `code/analysis/calibration.py`, which applies calibration factors, but it writes its log to `data/processed/calibration_log.json` and saves calibrated traces as a CSV. The required output file `data/processed/calibration_record.json` is missing, and the script never creates it. The task’s specification is therefore not satisfied.
- **T017a** — Checked `code/analysis/validation.py` (exists) and the required data files. The script does not compute the overall percentage of compliant runs nor enforce the 98 % compliance threshold, and the required input `data/processed/environment_logs.json` (and consequently the output `validation_flags.json`) are missing. Both the missing input file and the absent compliance‑percentage logic must be added to satisfy T017a.
- **T017b** — The repository contains the implementation `code/analysis/compliance.py`, but the required output artifact `data/processed/compliance_report.json` is missing, and there is no evidence that the script was run or that ≥95 % of runs met all tolerances. The task is not fulfilled until the compliance report file is generated (with a compliance percentage ≥0.95) and the file is present in the expected location.
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
