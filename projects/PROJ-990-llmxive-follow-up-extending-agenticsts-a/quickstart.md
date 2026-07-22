# llmXive Quickstart Guide

## Overview

This guide walks through the complete execution of the llmXive automated science pipeline
for the AgenticSTS follow-up project.

## Prerequisites

- Python 3.11+
- pip dependencies installed (see `requirements.txt`)
- Project structure initialized (T001)

## Installation

```bash
pip install -r requirements.txt
```

## Execution

Run the full pipeline:

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

This will execute all phases in order:
1. **Phase 1**: Setup (already completed)
2. **Phase 2**: Foundational (data parsing, splitting, ablation, validation)
3. **Phase 3**: User Stories 1 & 2 (Dynamic policy, baselines, aggregation)
4. **Phase 4**: Statistical Significance Reporting
5. **Polish**: Documentation and cleanup

## Individual Task Execution

If you need to run specific tasks independently:

### Data Processing
```bash
# Parse trajectories
python code/parser.py

# Split data
python code/splitter.py

# Calculate entropy
python code/entropy.py
```

### Ablation & Validation
```bash
# Run ablation study
python code/ablation.py

# Validate proxy correlation
python code/classifier.py
```

### Simulation & Baselines
```bash
# Run dynamic simulation
python code/simulator.py --policy dynamic

# Run static baseline
python code/baseline_static_runner.py

# Run random baseline
python code/simulator.py --policy random
```

### Aggregation & Statistics
```bash
# Generate baseline comparison
python code/generate_baseline_comparison.py

# Check token reduction
python code/token_reduction_verifier.py

# Check token consistency (T023)
python code/token_consistency_checker.py

# Run statistical tests
python code/stats.py
```

### Validation & Reporting
```bash
# Generate final statistical report
python code/generate_statistical_report.py

# Run quickstart validation
python code/run_quickstart_validation.py
```

## Output Artifacts

All processed data will be written to `data/processed/`:

- `metrics_with_moves.csv` - Parsed trajectory metrics
- `train_set.csv`, `validation_set.csv`, `test_set.csv` - Data splits
- `ablation_labels_*.json` - Ablation study results
- `simulation_logs_*.json` - Simulation outputs
- `baseline_comparison.csv` - Aggregated statistics
- `token_consistency_report.json` - Token savings consistency (T023)
- `statistical_results.json` - Final statistical analysis

## Troubleshooting

### Missing Data Files
Ensure `data/raw/` contains trajectory files (`.json`, `.jsonl`, `.log`).

### Pipeline Failures
Check `data/processed/edge_case_warnings.log` for specific error details.

### Memory Issues
Use `--dry-run` flag for a quick validation on a subset:
```bash
python code/quickstart_validator.py
```

## Next Steps

After successful execution, review the final reports in `data/processed/` and
proceed to Phase 4 (Statistical Significance) if not automatically completed.