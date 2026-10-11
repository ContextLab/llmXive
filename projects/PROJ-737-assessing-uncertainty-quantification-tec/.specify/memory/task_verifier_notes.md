# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories `data/raw/`, `data/processed/`, `data/results/`, and `figures/` are missing, and although `per_sample_errors.schema.yaml` exists under `specs/.../contracts/`, its contents have not been shown to confirm it defines the exact columns (`sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`). The implementer must add the missing directories and ensure the schema file contains the specified fields.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
