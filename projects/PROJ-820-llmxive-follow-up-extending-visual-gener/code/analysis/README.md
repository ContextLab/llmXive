# Analysis Module

This module contains tools for analyzing physics simulation contradictions and
performing statistical evaluation of experimental results.

## Components

### `contradiction_analyzer.py`

Analyzes physics simulation logs to detect logical contradictions and flag studies
that exceed acceptable rates.

**Key Functions:**
- `load_contradiction_log()`: Load contradiction log JSON
- `calculate_contradiction_rate()`: Calculate rate as percentage
- `verify_contradiction_rate()`: Check if rate is below threshold
- `flag_study_if_high_rate()`: Raise error if rate exceeds threshold
- `run_contradiction_analysis()`: Full analysis pipeline

**Usage:**
```bash
python code/analysis/contradiction_analyzer.py --log-dir data/derived/physics_constraints --total-scenes 100
```

### `statistics.py`

Provides statistical analysis for evaluating geometric consistency and prompt adherence.

**Key Functions:**
- `calculate_effect_size()`: Cohen's h for two proportions
- `power_analysis_two_proportions()`: Power analysis
- `two_proportion_z_test()`: Z-test for proportions
- `fisher_exact_test()`: Fisher's Exact Test
- `select_statistical_test()`: Auto-select test based on cell counts
- `run_power_analysis_and_report()`: Run power analysis and save report
- `run_statistical_comparison()`: Compare baseline vs experimental
- `generate_final_analysis_csv()`: Generate final summary CSV

**Usage:**
```bash
python code/analysis/statistics.py --baseline 0.1 --experimental 0.05 --n-per-group 100
```

## Output Files

- `data/processed/power_analysis_report.json`: Power analysis results
- `data/processed/statistical_comparison.json`: Statistical test results
- `data/processed/final_analysis.csv`: Aggregated summary with metrics

## Dependencies

- `numpy`
- `scipy`