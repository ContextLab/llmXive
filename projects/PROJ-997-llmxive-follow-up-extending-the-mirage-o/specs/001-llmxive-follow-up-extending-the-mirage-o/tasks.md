# Tasks: llmXive follow‑up — Hardware‑validated bounds on the quantization policy gap (MIPU)

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-llmxive-follow-up-extending-the-mirage-o/contracts/`, and any existing verified artifacts.

The study is organized into two research phases. All tasks are expressed as canonical checklist items of the form  

```
- [ ] T### [USx?] description … with file path(s)
    • verification: …
```

Only scientific‑level actions appear; generic scaffolding (directory creation, linting, platform‑state writes) is omitted because the platform supplies those utilities.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T015 [US001] Generate Ground Truth Data `code/cli/generate_ground_truth.py`   <!-- FAILED-IN-EXECUTION: code/cli/generate_ground_truth.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/generate_ground_truth.py exit=1; code/cli/validate_dataset_stats.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/generate_ground_truth.py exit=1; code/cli/validate_dataset_stats.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/generate_ground_truth.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/cli/generate_ground_truth.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/generate_ground_truth.py exit=1 -->
    • verification: script completes without error; Parquet file contains ≥ 100 successful samples per quantization level; `data/processed/dataset_stats.json` reports a statistically significant non‑zero KL portion (p < 0.05).

- [ ] T016 [US001] Validate Dataset Statistics `code/cli/validate_dataset_stats.py`   <!-- FAILED-IN-EXECUTION: code/cli/validate_dataset_stats.py exit=1 -->
    • verification: `dataset_stats.json` exists and contains the required statistics with p < 0.05.

- [ ] T019 [US001] Feature Extraction & Optional PCA `code/services/feature_extractor.py`  
    • verification: unit tests confirm correct numeric shapes and reproducibility across runs.

- [ ] T021 [US002] Load Training Data and Train Kernel Ridge Regression `code/cli/train_predictor.py`  
    • verification: `gap_predictor.pkl` loads; `data/processed/krr_sweep_results.json` records grid and chosen hyper‑parameters.

- [ ] T022 [US002] Evaluate Predictor Model `code/cli/evaluate_predictor.py`  
    • verification: `test_metrics.json` reports Pearson r ≥ 0.8 and MAE < 0.1 (or records the actual values).

- [ ] T023 [US002] Stratify Training Data `code/cli/prepare_splits.py`  
    • verification: split files exist; chi‑square p > 0.05 indicating balanced splits.

- [ ] T029 [US003] Implement Full Hardware‑Sync Baseline `code/cli/run_full_hardware_sync.py`  
    • verification: JSON file contains per‑prompt metrics and total runtime log.

## Phase 2 – Complete the study and validate its evidence  

- [ ] T009 [US003] Paired‑MIPU Benchmark `code/cli/run_paired_mipu.py`  
    • verification: both JSON files exist; t‑test fields (`statistic`, `p_value`, `bonferroni_corrected_p`, `conclusion`) are present.

- [ ] T010 [US003] Bound‑Consistency Verification `code/cli/verify_bound_consistency.py`  
    • verification: JSON includes all three levels; satisfaction ≥ 95 % for ε = 0.1 (or documents actual rates).

- [ ] T011 [US003] Latency Breakdown & Power Analysis `code/cli/latency_breakdown_analyzer.py`  
    • verification: both JSON files exist; `reduction_percentage` ≥ 90 % flagged, `power` ≥ 0.8 or a warning logged.

- [ ] T027 [US003] Verify Bound Consistency Across Levels `code/cli/verify_bound_consistency_across_levels.py`  
    • verification: JSON reports per‑level satisfaction ≥ 95 % for ε = 0.1.

- [ ] T028 [US003] Simulate MIPU Loop and Define Baseline Policy `code/cli/simulate_mipu_loop.py`  
    • verification: script runs end‑to‑end, produces `data/processed/mipu_simulation_results.json` containing per‑prompt decisions, predicted gaps, and baseline metrics; downstream tasks (e.g., T009) can consume this file.

- [ ] T030 [SC‑005] End‑to‑End Runtime Verification `code/cli/runtime_audit.py`  
    • verification: JSON contains `total_seconds` ≤ 21600 and `sample_count` ≥ 300.

- [ ] T031 [US003] Generalizability & Domain Sensitivity Check `code/cli/check_generalizability.py`  
    • verification: JSON fields are numeric and show no catastrophic drop in performance across difficulty bins.

- [ ] T032 [US003] Aggregate Bound Consistency Results `code/cli/aggregate_results.py`  
    • verification: `metrics.json` validates against the schema and includes all required sections (correlation_results, statistical_tests, latency_reduction, collinearity_check, etc.).

- [ ] T013 [US003] Write Final Research Report `docs/reports/001-llmxive-mipu-gap-bounds.md` and update `quickstart.md`  
    • verification: every figure referenced in the markdown exists; re‑running the command chain from a clean checkout reproduces all downstream artifacts.

---

## Dependencies & requirement coverage  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (feature extraction) | T019 |
| FR‑002 (CPU quantized inference) | T015 |
| FR‑003 (exact KL) | T015 |
| FR‑004 (joint KRR) | T021 |
| FR‑005 (Pearson r on held‑out) | T022 |
| FR‑006 (paired t‑test) | T009, T029, T028 |
| FR‑007 (bound consistency) | T010, T027, T032 |
| SC‑001 (r > 0.8) | T022 |
| SC‑002 (≥ 90 % latency reduction) | T011 |
| SC‑003 (p > 0.05) | T009 |
| SC‑004 (bound consistency across levels) | T010, T027 |
| SC‑005 (≤ 6 h, n ≥ 300) | T030 |
| Edge‑case handling | T015 (zero KL), T019 (flat gradients), T015 (engine load errors) |

**Execution order**:  
T015 → T016 → T019 → T023 → T021 → T022 → T029 → T028 → T009 → T010 → T027 → T011 → T030 → T031 → T032 → T013.

All tasks are unchecked (`- [ ]`) pending implementation; completed work from prior runs is preserved via the artifact paths indicated above.  