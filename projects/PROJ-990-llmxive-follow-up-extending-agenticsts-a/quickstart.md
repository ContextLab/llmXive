# llmXive Quickstart Guide

This guide provides the commands to run the full llmXive pipeline for the AgenticSTS follow-up project.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- Raw trajectory data in `data/raw/` (JSON, JSONL, or LOG files)

## Quickstart Commands

Run the following commands in order to execute the full pipeline:

1. **Initialize and Parse Data**
 ```bash
 python code/parser.py
 ```
 *Output*: `data/processed/metrics_with_moves.csv`, `data/processed/edge_case_warnings.log`

2. **Split Dataset**
 ```bash
 python code/splitter.py
 ```
 *Output*: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`, `data/processed/validation_set_ids.json`

3. **Extract Static Proxy (Validation Set Only)**
 ```bash
 python code/parser.py --extract-static-proxy
 ```
 *Output*: `data/processed/static_log_proxy.json`

4. **Run Ablation Study (Train Set)**
 ```bash
 python code/ablation.py --dataset train_set
 ```
 *Output*: `data/processed/ablation_labels_train.json`

5. **Run Ablation Study (Validation Set)**
 ```bash
 python code/ablation.py --dataset validation_set
 ```
 *Output*: `data/processed/ablation_labels_validation.json`

6. **Validate Sample Count and Generate Fallback Flag**
 ```bash
 python code/validator.py
 ```
 *Output*: `data/processed/fallback_flag.json`

7. **Validate Proxy Correlation and Train Classifier**
 ```bash
 python code/classifier.py
 ```
 *Output*: `models/layer_utility_classifier.pkl`, `data/processed/proxy_validation_report.json`

8. **Run Simulations (Dynamic, Static, Random)**
 ```bash
 python code/simulator.py --policy dynamic
 python code/simulator.py --policy static
 python code/simulator.py --policy random
 ```
 *Output*: `data/processed/simulation_logs_dynamic.json`, `data/processed/simulation_logs_static.json`, `data/processed/simulation_logs_random.json`

9. **Aggregate Baseline Comparisons**
 ```bash
 python code/stats.py --aggregate
 ```
 *Output*: `data/processed/baseline_comparison.csv`

10. **Verify Token Reduction**
 ```bash
 python code/token_reduction_verifier.py
 ```
 *Output*: `data/processed/token_reduction_verification.json`

11. **Check Token Consistency**
 ```bash
 python code/token_consistency_checker.py
 ```
 *Output*: `data/processed/token_consistency_report.json`

12. **Detect Trajectory Divergence**
 ```bash
 python code/stats.py --detect-divergence
 ```
 *Output*: `data/processed/divergence_report.json`

13. **Run Statistical Tests**
 ```bash
 python code/stats.py --test
 ```
 *Output*: `data/processed/statistical_results.json`

14. **Generate Final Statistical Report**
 ```bash
 python code/generate_statistical_report.py
 ```
 *Output*: `data/processed/statistical_results.json` (updated)

15. **Generate Analysis Config Snapshot (Reproducibility)**
 ```bash
 python code/generate_analysis_config.py
 ```
 *Output*: `data/processed/analysis_config.json`

16. **Run Benchmark**
 ```bash
 python code/benchmark.py
 ```
 *Output*: `data/processed/benchmark_log.json`

17. **Generate Optimization Report**
 ```bash
 python code/optimization_report.py
 ```
 *Output*: `data/processed/optimization_report.md`

## Full Pipeline Execution

Alternatively, run the entire pipeline with a single command:
```bash
python code/main.py
```

## Validation

To validate the pipeline outputs:
```bash
python code/quickstart_validator.py
```

## Cleanup

To run code quality checks:
```bash
python code/cleanup_runner.py
```
