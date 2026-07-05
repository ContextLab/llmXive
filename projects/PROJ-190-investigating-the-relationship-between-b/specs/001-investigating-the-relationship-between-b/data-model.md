# Data Model: Brain Network Efficiency and Fluid Intelligence

## 1. Entity Relationship Overview

The data model consists of three primary entities: `Subject`, `BrainNetwork`, and `StatisticalResult`.

- **Subject**: Represents an individual participant. Contains demographic data and behavioral scores.
- **BrainNetwork**: Represents the graph representation of a subject's brain. Contains the connectivity matrix and derived efficiency metrics.
- **StatisticalResult**: Aggregated results from the analysis (correlations, regression coefficients, p-values).

## 2. Data Schemas

### Subject Schema
Contains raw and derived subject-level data.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | `string` | Unique HCP subject identifier. | HCP Metadata |
| `fluid_intelligence` | `float` | NIH Toolbox Fluid Intelligence composite score. | HCP Behavioral |
| `age` | `integer` | Age in years. | HCP Metadata |
| `sex` | `string` | 'M' or 'F'. | HCP Metadata |
| `mean_fd` | `float` | Mean Framewise Displacement (mm). | Preprocessing |
| `excluded` | `boolean` | True if excluded (missing score, high motion, disconnected graph). | Pipeline Logic |

### BrainNetwork Schema
Contains graph metrics per subject.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `subject_id` | `string` | Foreign key to Subject. | Subject |
| `atlas_resolution` | `string` | '200_ROI' or '400_ROI'. | Config |
| `graph_type` | `string` | 'binary', 'weighted', or 'absolute'. | Config |
| `density` | `float` | Actual edge density (target ~0.20). | Thresholding |
| `global_efficiency` | `float` | Global efficiency (Harmonic Mean if disconnected). | Graph Metric |
| `fp_efficiency` | `float` | Frontoparietal subgraph efficiency. | Graph Metric |
| `is_disconnected` | `boolean` | Flag if graph was disconnected (used for exclusion logic). | Graph Metric |

### StatisticalResult Schema
Contains final analysis outputs.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `metric_name` | `string` | 'global_efficiency' or 'fp_efficiency'. | Analysis |
| `graph_type` | `string` | 'binary' (primary) or 'absolute'/'weighted' (robustness). | Analysis |
| `correlation_r` | `float` | Pearson/Spearman correlation coefficient. | Stats |
| `p_value_uncorrected` | `float` | Raw p-value. | Stats |
| `p_value_fwe` | `float` | Family-wise error corrected p-value (only for primary binary tests). | Permutation |
| `regression_coef` | `float` | Coefficient from multiple regression. | Stats |
| `vif` | `float` | Variance Inflation Factor. | Stats |
| `is_primary` | `boolean` | True if part of the FWE-corrected family. | Analysis |

## 3. File Structure

```text
data/
├── raw/
│   ├── sub-XXXX/
│   │   └── rfMRI_REST1_LR.nii.gz
│   └── behavioral.csv
├── processed/
│   ├── time_series/
│   │   └── sub-XXXX_200ROI.npy
│   ├── matrices/
│   │   └── sub-XXXX_200ROI_binary.npy
│   └── metrics/
│       └── efficiency_metrics.csv
└── results/
    └── statistical_summary.json
```

**Versioning Note**: All checksums for files in `data/` are recorded in `state/*.yaml` as the Single Source of Truth (Constitution Principle III).