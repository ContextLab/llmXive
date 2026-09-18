# User Guide

## Introduction

This guide explains how to use the Digital Decluttering research pipeline to analyze the effects of digital interventions on cognitive performance and well-being.

## Workflow Overview

1. **Data Collection**: Gather baseline and post-intervention data.
2. **Preprocessing**: Parse logs and validate data quality.
3. **Scoring**: Calculate psychometric scores.
4. **Analysis**: Perform statistical tests and calculate effect sizes.
5. **Reporting**: Generate comprehensive reports.

## Step-by-Step Instructions

### 1. Preparing Your Data

Ensure your data files are located in the correct directories:
- `data/raw/`: Raw baseline and post-intervention data.
- `data/compliance/`: Daily compliance logs.

**File Formats**:
- CSV for tabular data.
- JSON for structured logs.

### 2. Running the Pipeline

Execute the pipeline scripts in order:

```bash
# 1. Collect and validate baseline
python code/pipeline/collect_baseline.py

# 2. Process compliance logs
python code/pipeline/aggregate_compliance.py

# 3. Merge datasets
python code/pipeline/merge_data.py

# 4. Calculate change scores
python code/analysis/change_scores.py

# 5. Run statistical analysis
python code/analysis/statistical_summary.py

# 6. Generate report
python code/report/generate_report.py
```

### 3. Interpreting Results

**Statistical Summary (`results/statistical_summary.json`)**:
- `mean_change`: Average difference between post and baseline.
- `ci_95`: 95% confidence interval.
- `p_value_corrected`: Holm-Bonferroni corrected p-value.

**Final Report (`results/final_report.md`)**:
- Includes effect sizes, power analysis, and sensitivity analysis.

### 4. Customizing the Analysis

Modify parameters in `code/config/env_config.py`:
- `bootstrap_resamples`: Number of resamples for CI (default: 10,000).
- `alpha_level`: Significance threshold (default: 0.05).

### 5. Troubleshooting Common Issues

- **Data Mismatch**: Ensure participant IDs match across baseline and post files.
- **Missing Values**: The pipeline handles missing data by excluding incomplete records.
- **Convergence Failures**: If bootstrapping fails, the Wilcoxon fallback is automatically triggered.

## Advanced Usage

### Running Specific Analyses

To run only the power simulation:
```bash
python code/analysis/power_simulation.py
```

To generate only visualizations:
```bash
python code/viz/generate_plots.py
```

### Integrating New Metrics

1. Add scoring logic in `code/scoring/`.
2. Update `contracts/dataset.schema.yaml`.
3. Modify `code/analysis/statistical_summary.py` to include the new metric.

## Support

For issues or questions, please refer to the `README.md` or contact the project maintainers.
