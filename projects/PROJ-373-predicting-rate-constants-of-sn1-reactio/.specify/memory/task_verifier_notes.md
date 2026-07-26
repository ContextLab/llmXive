# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The repository contains a `code/data/descriptors.py` file, but it does not show any code that writes descriptor information to `data/processed/descriptor.log`, and the required log file is absent. Consequently the task’s output requirement is not met.
- **T012** — The provided `code/data/clean.py` is truncated (ends mid‑string) and does not show the logic that reads `intermediate_sn1.csv`, applies the proxy filter, writes the cleaned CSV, generates `pre_filter_distribution.json`, or logs exclusions. Moreover, the required input file `data/processed/intermediate_sn1.csv` and the expected log file `data/processed/clean.log` are absent. The task’s core functionality and required artifacts are therefore not present.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/clean.log, data/processed/descriptor.log, data/processed/exclusion_report.csv, schema.yaml
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_sn1.csv
- **T028** — The repository contains a partially‑implemented `code/analysis/collinearity.py` (truncated and not shown to produce a markdown report) and the required input `data/processed/cleaned_sn1.csv` is absent, so the script cannot be executed nor can the `artifacts/collinearity_report.md` be generated. The missing dataset and final report must be added for the task to be considered complete.
