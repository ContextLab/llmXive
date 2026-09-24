# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014b** — The provided `src/ingest/fetch_thermal.py` is truncated and does not show the actual data‑fetching, validation, and CSV‑writing logic required by T014b, and the expected output file `data/raw/thermal_raw.csv` is absent. Consequently the implementation cannot be confirmed to meet the specification.
- **T014** — The provided `provenance_validator.py` is truncated and contains errors (e.g., an incomplete variable name `reaso`), uses an incorrect NIST ID regex, never writes `data/cleaned/provenance_report.json`, and does not implement the required exit‑code behavior. The expected JSON report file is also missing.
- **T021d** — The repository lacks a `data/descriptors.csv` file, so no descriptors are being written out, and the provided excerpt of `src/descriptors/compute_descriptors.py` does not show an implementation of the required `compute_unit_cell_volume(structure)` function. Both the essential function and the required output file are missing.
- **T023** — The repository lacks the required input CSV (`data/cleaned/descriptors_vif_filtered.csv`) and the expected result files (`data/results/stratified_summary.md`, `data/results/correlation_matrix.json`). Moreover, the provided `src/analysis/correlation.py` is truncated and does not show CLI argument handling, file I/O, or generation of the specified outputs, so it does not demonstrably fulfill the task’s functional requirements.
- **T023c** — declared artifact(s) missing/empty/invalid: src/utils/sensitivity.py, data/results/sensitivity_analysis.json
- **T042** — declared artifact(s) missing/empty/invalid: src/main.py, data/cleaned/merged_perovskite.csv
- **T043** — declared artifact(s) missing/empty/invalid: data/results/correlation_matrix.json
- **T047** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_analysis.json
