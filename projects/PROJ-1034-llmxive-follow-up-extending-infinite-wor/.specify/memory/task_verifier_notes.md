# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The evidence includes all required `src/*/__init__.py` files and the two `data/*/.gitkeep` files, but the `docs/.gitkeep` and `state/.gitkeep` files are absent from the listed artifacts. These missing files prevent the task from being fully satisfied.
- **T004** — The file `src/sim/eco_director.py` exists but its `_step()` is an explicit placeholder ("Placeholder for actual CA logic") that fabricates metrics (coherence_score=0.0, diversity_score=0.0, step_latency=0.0) with no real CA update logic, and the memory check is a stub. The task's core requirements — schema definition, a real update loop, and a runtime parameter injection mechanism (CLI args + YAML loader) — are entirely absent: there is no CLI argument parsing, no YAML loader, and no parameter injection anywhere in the artifact.
- **T006d** — declared artifact(s) missing/empty/invalid: tests/unit/test_termination_signal.py
- **T006d1** — declared artifact(s) missing/empty/invalid: tests/integration/test_termination_trigger.py
- **T006d2_test** — declared artifact(s) missing/empty/invalid: tests/integration/test_log_content.py
- **T060** — declared artifact(s) missing/empty/invalid: src/analysis/power_analysis.py
- **T016a** — declared artifact(s) missing/empty/invalid: config/default.yaml
- **T016c** — declared artifact(s) missing/empty/invalid: tests/integration/test_baseline_partial.py, data/raw/baseline_partial.parquet
- **T020c** — declared artifact(s) missing/empty/invalid: data/processed/lmm_results.csv
- **T024** — declared artifact(s) missing/empty/invalid: src/analysis/filter.py
- **T028** — declared artifact(s) missing/empty/invalid: src/analysis/anova_runner.py
- **T032c** — declared artifact(s) missing/empty/invalid: data/processed/config_consumption_log.json
- **T054** — declared artifact(s) missing/empty/invalid: src/analysis/acm_validator.py
- **T063a** — declared artifact(s) missing/empty/invalid: data/processed/acf_adjustment_log.json
- **T063** — declared artifact(s) missing/empty/invalid: src/analysis/verify_acf_adjustment.py
- **T070** — declared artifact(s) missing/empty/invalid: src/analysis/verify_streaming.py
- **T029b** — declared artifact(s) missing/empty/invalid: docs/sensitivity_report.md
- **T030a** — declared artifact(s) missing/empty/invalid: src/analysis/parity_test.py
- **T067** — declared artifact(s) missing/empty/invalid: src/analysis/latency_calc.py
- **T030b** — declared artifact(s) missing/empty/invalid: src/analysis/latency_calc.py
- **T033** — declared artifact(s) missing/empty/invalid: docs/report.md, data/processed/summary.csv, docs/report_template.md
- **T055** — declared artifact(s) missing/empty/invalid: src/analysis/latency_calc.py
- **T058** — declared artifact(s) missing/empty/invalid: src/analysis/parity_test.py
- **T062** — declared artifact(s) missing/empty/invalid: src/analysis/verify_sc006.py, data/processed/sc006_status.json
- **T068** — declared artifact(s) missing/empty/invalid: src/analysis/verify_acf_adjustment.py
- **T071** — declared artifact(s) missing/empty/invalid: src/analysis/latency_calc.py, data/processed/permutation_seed.json
- **T073** — declared artifact(s) missing/empty/invalid: src/analysis/verify_novelty_independence.py
