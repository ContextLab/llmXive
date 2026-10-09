# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000c** — The required test `tests/unit/test_power_analysis.py::test_output_power` does not exist; the file contains only tests of a locally replicated function, none of which reads N from the script's output or checks achieved power using `statsmodels.stats.power` utilities (the imported `tt_solve_power` is never used). The script itself exists and computes N≈85, but the task's specific verification mechanism — a test that parses script output and confirms power ≥ 0.80 for r ≥ 0.3 via statsmodels — is missing, and there is no execution evidence any test ran.
- **T000d** — Both required artifacts are missing: `code/power_analysis_output.txt` does not exist and neither does the verification test `tests/unit/test_power_output_persistence.py`. There is no evidence on disk that any sample size N was calculated or persisted, so the task's core requirement is unmet.
- **T001b** — The orchestrator module exists and implements the runtime monitor logic (elapsed-time tracking, 6-hour limit, warning flag, non-fatal behavior), but the required CI verification artifact `tests/unit/test_runtime_monitor.py` — including the specifically named `test_warning_flag` assertion — is MISSING from disk, so there is no evidence the runtime metric logging or warning-flag behavior is tested. The implementer must add the unit test file verifying that the runtime metric is logged and the warning flag is set when elapsed time exceeds 6 hours.
- **T001** — The evidence only confirms the project root and top-level `code/` and `data/` directories exist; there is no confirmation that the specific required subdirectories (`code/utils`, `code/tests/unit`, `code/tests/integration`, `data/raw`, `data/networks`, `data/transport`, `data/analysis`, `plots`, `state/projects`) were actually created. Additionally, the referenced verification test `test_directories_exist` does not exist — the on-disk test is a different test (`test_create_directories_creates_all_paths` testing a `setup_project_structure.create_directories` function whose module is not shown t
- **T017** — declared artifact(s) missing/empty/invalid: tests/unit/test_connectivity_gate.py
- **T018** — declared artifact(s) missing/empty/invalid: tests/unit/test_physical_stability_gate.py
- **T019** — declared artifact(s) missing/empty/invalid: tests/unit/test_cutoff_scaling_gate.py
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/force_constants/, tests/unit/test_force_constants_derivation.py
- **T031** — declared artifact(s) missing/empty/invalid: code/compute_transport.py, data/networks/, tests/integration/test_compute_transport.py
- **T031b** — declared artifact(s) missing/empty/invalid: code/compute_transport.py, tests/unit/test_regime_detection.py
- **T031c** — declared artifact(s) missing/empty/invalid: tests/unit/test_sensitivity_stability.py
- **T032** — declared artifact(s) missing/empty/invalid: tests/unit/test_convergence_retry.py
- **T025** — declared artifact(s) missing/empty/invalid: tests/integration/test_ensemble_generation.py
- **T027** — declared artifact(s) missing/empty/invalid: state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml, tests/unit/test_checksum_record.py
- **T037** — declared artifact(s) missing/empty/invalid: code/analyze_correlations.py, data/analysis/correlation_results.csv, tests/unit/test_correlation_analysis.py
- **T038** — declared artifact(s) missing/empty/invalid: tests/unit/test_bootstrap_iterations.py
- **T040** — declared artifact(s) missing/empty/invalid: tests/unit/test_multiple_comparison_correction.py
- **T042** — declared artifact(s) missing/empty/invalid: tests/unit/test_power_law_fit.py
- **T044** — declared artifact(s) missing/empty/invalid: data/analysis/plots/metric_vs_kappa.png, tests/unit/test_plot_generation.py
- **T045** — declared artifact(s) missing/empty/invalid: data/analysis/plots/powerlaw_fit.png, tests/unit/test_plot_generation.py
- **T068** — declared artifact(s) missing/empty/invalid: data/metadata/graph_manifest.json, tests/unit/test_graph_manifest.py
