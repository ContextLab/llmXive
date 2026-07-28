# Quickstart Guide: llmXive Follow-up (AgenticSTS Extension)

This guide provides the exact commands to run the full pipeline from a clean environment.
All commands should be run from the project root directory.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Step-by-Step Execution

### 1. Setup and Configuration
```bash
# Ensure project structure exists
python code/config.py
```

### 2. Bootstrap Synthetic Data (If needed)
```bash
# T006a: Bootstrap synthetic data if data/raw/ is empty
python code/bootstrap_data.py
```

### 3. Parse Trajectories and Extract Metrics
```bash
# T006: Parse raw trajectories and extract metrics with move distributions
python code/parser.py
```

### 4. Generate No-Data Warning (If T006 was skipped)
```bash
# T005a: Generate warning log if no trajectory data exists
python code/t005a_no_data_warning.py
```

### 5. Calculate Entropy
```bash
# T005: Calculate Shannon entropy of legal move distributions
python code/entropy.py
```

### 6. Split Data
```bash
# T014a: Stratified split into Train, Ablation-Train, Validation, Test sets
python code/splitter.py
```

### 7. Extract Static Proxy
```bash
# T007c: Extract static-log-derived utility for validation set
python code/proxy_extractor.py
```

### 8. Run Ablation Study
```bash
# T008: Generate ground truth labels for Ablation-Train set
python code/ablation.py --dataset ablation_train_set
# T008b: Generate ground truth labels for Validation set
python code/ablation.py --dataset validation_set
```

### 9. Check Sample Size and Set Fallback Flag
```bash
# T008c: Check sample count and generate fallback flag
python code/check_sample_size.py
```

### 10. Validate Proxy
```bash
# T014: Validate proxy correlation against ablation ground truth
python code/classifier.py --mode validate_proxy
```

### 11. Train Classifier
```bash
# T009: Train lightweight classifier on ablation labels
python code/classifier.py --mode train
```

### 12. Run Simulations
```bash
# T017: Run dynamic simulation on test set
python code/run_dynamic_simulation.py
# T019: Run static baseline simulation
python code/baseline_static_runner.py
# T020: Run random baseline simulation
python code/engine_runner.py --policy random
```

### 13. Aggregate and Analyze Results
```bash
# T021: Aggregate simulation results
python code/generate_baseline_comparison.py
# T022a: Verify token reduction
python code/token_reduction_verifier.py
# T024a: Detect trajectory divergence
python code/stats.py --mode divergence
# T025: Run statistical tests
python code/stats.py --mode statistical_test
# T028: Generate final statistical report
python code/generate_statistical_report.py
```

### 14. Validation and Reporting
```bash
# T016a: Verify edge case warnings
python code/quickstart_validator.py
# T033: Run full quickstart validation
python code/quickstart_runner.py
# T031: Benchmark performance
python code/benchmark.py
```

## Expected Outputs

All processed data will be written to `data/processed/`:
- `metrics_with_moves.csv`
- `edge_case_warnings.log`
- `train_set.csv`, `ablation_train_set.csv`, `validation_set.csv`, `test_set.csv`
- `validation_set_ids.json`
- `static_log_proxy.json`
- `ablation_labels_train.json`, `ablation_labels_validation.json`
- `fallback_flag.json`
- `proxy_validation_report.json`
- `simulation_logs_dynamic.json`, `simulation_logs_static.json`, `simulation_logs_random.json`
- `baseline_comparison.csv`
- `token_reduction_verification.json`
- `divergence_report.json`
- `statistical_results.json`
- `analysis_config.json`

## Troubleshooting

- If `data/raw/` is empty, ensure T006a has run to bootstrap synthetic data.
- If entropy calculation fails, check `data/processed/edge_case_warnings.log` for specific errors.
- If validation set size < 20, the pipeline will raise a `ValueError` as per FR-006.
- If token reduction verification fails, check `data/processed/verification_failed.json` for details.