# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The provided `contracts/output.schema.yaml` exists but its contents do not match the task specification. It defines a single, extensive analysis schema rather than four separate JSON schemas with the exact required keys: (1) Mann‑Whitney U results lack a `method` field and use `p_value` instead of `pvalue`; (2) VIF diagnostics are embedded in a regression object instead of a schema with `predictor` and `vif_score`; (3) Power analysis schema uses `sample_size_a`, `sample_size_b`, `effect_size`, etc., and omits `min_detectable_effect`; (4) No schema for error reports (`error_code`, `observed_cou
- **T017a** — Requested task execution failed; rerun successfully: code/data/generate_audit_sample.py exit=1
- **T032** — declared artifact(s) missing/empty/invalid: code/analysis/viz.py, docs/reports/boxplot_comment_count.png, docs/reports/boxplot_sentiment.png, docs/reports/boxplot_merge_time.png
- **T033** — declared artifact(s) missing/empty/invalid: code/analysis/viz.py, docs/reports/histogram_comment_count.png, docs/reports/histogram_sentiment.png
- **T037** — declared artifact(s) missing/empty/invalid: docs/research.md, docs/quickstart.md
- **T041a** — declared artifact(s) missing/empty/invalid: code/benchmark/run_time.py
