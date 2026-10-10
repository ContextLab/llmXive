# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002b** — The `data/` directory and its required subfolders (`raw`, `processed`, `metrics`, `logs`, `models`) are present, but there is no artifact (script output, test log, etc.) showing that `os.path.isdir` was actually run and confirmed for each path. Provide evidence of the verification step (e.g., a test script and its successful output).
- **T002f** — The `tests/` directory and its three subdirectories are present, satisfying the creation part, but there is no evidence (e.g., a script run, log output, or test result) showing that `os.path.isdir` was actually executed to verify those paths as required. Provide proof of the verification step.
- **T016_pre** — declared artifact(s) missing/empty/invalid: code/data/power_analysis_pre.py, data/metrics/theoretical_defaults.json, data/metrics/pre_extraction_sample_size.txt
- **T078** — declared artifact(s) missing/empty/invalid: code/data/verify_event_counts.py
- **T013b** — declared artifact(s) missing/empty/invalid: code/data/calculate_frame_complexity.py, data/processed/raw_extract.parquet, data/processed/complexity_added.parquet
- **T015** — declared artifact(s) missing/empty/invalid: code/data/validate_sampling_distribution.py, data/logs/sampling_distribution.log
- **T016_post** — declared artifact(s) missing/empty/invalid: data/metrics/power_analysis_final.json
- **T024a** — declared artifact(s) missing/empty/invalid: code/metrics/uncertainty_calibration.py
- **T024d** — declared artifact(s) missing/empty/invalid: code/tests/unit/test_memory_profile.py
- **T072** — declared artifact(s) missing/empty/invalid: code/metrics/two_stage_validation.py
- **T076** — declared artifact(s) missing/empty/invalid: code/utils/log_power_failure.py
- **T080** — declared artifact(s) missing/empty/invalid: code/metrics/verify_uncertainty_calibration.py
- **T047** — declared artifact(s) missing/empty/invalid: data/processed/counterfactual_indices.json, data/logs/counterfactual_log.txt
- **T060_Exec** — declared artifact(s) missing/empty/invalid: code/inference/full_solver.py, data/artifacts/baseline/
- **T060** — declared artifact(s) missing/empty/invalid: code/metrics/generate_counterfactual_fid.py, code/inference/full_solver.py
- **T050a** — declared artifact(s) missing/empty/invalid: code/inference/hybrid_engine.py
- **T050c_impl** — declared artifact(s) missing/empty/invalid: code/inference/generate_hybrid_output.py, data/artifacts/hybrid/
- **T050d** — declared artifact(s) missing/empty/invalid: code/inference/log_precedence.py, data/logs/precedence_log.json
- **T075** — declared artifact(s) missing/empty/invalid: code/inference/verify_precedence.py
- **T071a** — declared artifact(s) missing/empty/invalid: code/metrics/calculate_propensity_scores.py
- **T071b** — declared artifact(s) missing/empty/invalid: code/metrics/propensity_score_matching.py, data/processed/matched_dataset.parquet
- **T045** — declared artifact(s) missing/empty/invalid: code/metrics/analyze_latency_bias.py, data/metrics/latency_bias_analysis.json
- **T049** — declared artifact(s) missing/empty/invalid: code/metrics/tost_quality.py, data/metrics/fid_tost_results.json
- **T077** — declared artifact(s) missing/empty/invalid: code/metrics/log_human_data_fallback.py, data/logs/mos_validation.log
- **T079** — declared artifact(s) missing/empty/invalid: code/metrics/verify_fid_stability.py
