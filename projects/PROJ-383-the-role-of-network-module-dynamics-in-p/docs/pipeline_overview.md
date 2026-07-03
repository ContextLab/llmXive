# Pipeline Overview

This document provides a high-level overview of the `llmXive` pipeline for analyzing network module dynamics in predicting working memory.

## Architecture

The pipeline is structured into three main phases corresponding to the user stories:

1. **Data Ingestion and Preprocessing (US1)**
2. **Dynamic Flexibility Metric Computation (US2)**
3. **Statistical Analysis and Reporting (US3)**

Each phase is independent and can be tested separately.

## Data Flow

1. **Raw Data (OpenNeuro ds001734)**
 - Resting-state fMRI (rs-fMRI)
 - Behavioral scores (2-back task)
 - Motion parameters

2. **Preprocessing**
 - Motion scrubbing (FD > 0.2mm)
 - Regression of motion parameters
 - Exclusion of high-motion subjects (mean FD > 0.2mm)

3. **Dynamic Connectivity**
 - Sliding window correlation
 - Multilayer Modularity Optimization (MMO)
 - Flexibility metric calculation

4. **Statistical Analysis**
 - Partial Spearman correlation (controlling for motion)
 - Permutation testing (1,000 permutations)
 - Sensitivity analysis (window length robustness)

5. **Reporting**
 - JSON report with associational findings
 - Visualizations (null distribution, sensitivity plot)

## Key Constraints

- **Memory**: Pipeline enforces ≤7GB RAM limit.
- **Reproducibility**: All random seeds are pinned.
- **Data Integrity**: Checksums are computed and verified.
- **Motion Control**: Explicit motion scrubbing and regression.
- **Associational Framing**: All results are framed as associational, not causal.

## File Structure

```
code/
├── ingestion/
│ ├── download_hcp.py
│ ├── preprocess.py
│ ├── consolidate_data.py
│ ├── validate_source.py
│ └──...
├── analysis/
│ ├── dynamic_connectivity.py
│ ├── statistics.py
│ ├── sensitivity_analysis.py
│ └──...
├── results/
│ ├── generate_report.py
│ ├── generate_plots.py
│ └──...
├── utils/
│ ├── config.py
│ ├── memory_monitor.py
│ └── logging_config.py
└──...

data/
├── raw_fmri/
├── raw_behavior/
├── processed/
│ ├── scrubbed_timeseries.parquet
│ ├── flexibility_scores.parquet
│ └── consolidated_data.parquet
└── results/
 ├── statistical_report.json
 ├── sensitivity_analysis.json
 └── plots/
 ├── null_dist.png
 └── sensitivity_plot.png
```

## Execution Order

1. `initialize_directories.py`
2. `validate_source.py`
3. `download_hcp.py`
4. `preprocess.py`
5. `consolidate_data.py`
6. `dynamic_connectivity.py`
7. `output_flexibility_scores.py`
8. `statistics.py`
9. `sensitivity_analysis.py`
10. `generate_report.py`
11. `generate_plots.py`
