# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The results JSON itself is genuine (top eigenvalue 2.878256853596114 matches the historical execution log, run_id consistency and FR-004 outlier rule hold), but two required artifacts fail: `data/logs/simulation_run.log` is 0 bytes (the task requires logs written there), and both `simulation_run.schema.yaml` and `eigenvalue_result.schema.yaml` are MISSING, so verification criterion (a) — JSON validating against both contracts — cannot be satisfied. Additionally, the recorded `support_density` is 0.001 whereas the task's contract specifies `null` for the diagonal pattern.
- **T003** — Requested task execution failed; rerun successfully: code/analysis/apply_outlier_rule.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/analysis/threshold_identification_t004.py exit=1
