# Data Model: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

## Overview

This document defines the data structures, schemas, and file formats used throughout the pipeline. All data is stored in `data/` with checksums recorded.

## File Structure

```text
data/
├── raw/
│   ├── ds000278/            # Raw OpenNeuro download (HCP rs-fMRI)
│   └── checksums.json       # SHA-256 hashes of raw files
├── preprocessed/
│   ├── sub-*/               # fMRIPrep outputs (cleaned NIfTI, confounds TSV)
│   └── connectivity/        # 400x400 correlation matrices (NPY/CSV)
├── motion/
│   └── motion_metrics.csv   # Mean FD, max FD per participant (threshold: 0.3 mm)
├── results/
│   ├── baseline_metrics.csv # Network metrics per participant
│   ├── pca_components.csv   # PCA-transformed metrics
│   ├── model_summary.csv    # Regression coefficients, p-values, CIs
│   ├── power_analysis.txt   # Power analysis output
│   └── effect_sizes.pdf     # Visualization output
└── logs/
    └── pipeline_log.json    # Execution log with exclusion counts
```

## Entity Definitions

### Participant
- **ID**: String (e.g., `sub-1001`)
- **Age**: Integer
- **Sex**: String ('M', 'F')
- **WM_Score**: Float (N-back d-prime)
- **Mean_FD**: Float (framewise displacement)
- **Exclusion_Reason**: String (null if valid)

### ConnectivityMatrix
- **Shape**: 400 x 400
- **Type**: Symmetric Pearson correlation coefficients
- **Storage**: NPY or CSV in `data/preprocessed/connectivity/`

### NetworkMetrics
- **Global_Efficiency**: Float
- **Modularity_Q**: Float
- **FPN_Strength**: Float (average edge weight within FPN)
- **DMN_Strength**: Float (average edge weight within DMN)

## Data Flow

1. **Download**: Raw data fetched from OpenNeuro (`ds000278`). Checksums verified.
2. **Preprocess**: fMRIPrep generates cleaned NIfTI and confounds TSV.
3. **Validate**: ID matching and motion exclusion (FD > 0.3 mm).
4. **Extract**: Time series extracted via the Schaefer atlas parcellation; correlation matrices computed.
5. **Aggregate**: Network metrics calculated and saved to `baseline_metrics.csv`.
6. **Transform**: PCA applied to network metrics; components saved to `pca_components.csv`.
7. **Model**: Regression fit on PCA components; results saved to `model_summary.csv`.
8. **Visualize**: PDF report generated.