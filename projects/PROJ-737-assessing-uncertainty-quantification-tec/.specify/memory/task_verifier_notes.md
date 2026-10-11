# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directories `data/processed/`, `data/results/`, and `figures/` are reported MISSING, which the task explicitly requires to exist. Additionally, the schema evidence (`per_sample_errors_schema_example.csv` / `.json`) lists only `sample_id, method, prediction, lower_bound, upper_bound, ground_truth, dataset` — the required `abs_error` column is absent, so the data contract does not match the task's specified columns (the `per_sample_errors.schema.yaml` in `specs/.../contracts/` exists but its content was not shown to include `abs_error`, and the example contradicts it). The implementer must c
- **T002** — Requested task execution failed; rerun successfully: code/download.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
