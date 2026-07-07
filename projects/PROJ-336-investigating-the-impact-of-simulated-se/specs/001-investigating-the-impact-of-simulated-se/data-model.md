# Data Model: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

## Overview

This document defines the data structures used throughout the project. All data is stored in compressed formats (`.npy`, `.csv`) to stay within the 14GB disk limit. The model is designed to support the preprocessing, analysis, and visualization pipeline.

## Entities

### 1. Subject

Represents a single research participant.

| Attribute | Type | Description | Source Script |
|-----------|------|-------------|---------------|
| `subject_id` | `str` | Unique identifier for the subject (e.g., "sub-001"). | `src/data/download.py` |
| `condition` | `str` | "pre" or "post" deprivation. | `src/data/download.py` |
| `motion_fd_mean` | `float` | Mean Framewise Displacement (calculated from residual motion parameters). | `src/data/quality_check.py` |
| `motion_fd_max` | `float` | Maximum Framewise Displacement (calculated from residual motion parameters). | `src/data/quality_check.py` |
| `excluded` | `bool` | True if subject exceeds motion threshold (FD > 0.5mm in > 10% volumes). | `src/data/quality_check.py` |
| `pre_bold_path` | `str` | Path to pre-deprivation BOLD time series file. | `src/data/preprocess.py` |
| `post_bold_path` | `str` | Path to post-deprivation BOLD time series file. | `src/data/preprocess.py` |

### 2. Connectivity Matrix

Represents functional connectivity between all ROI pairs for a subject and condition.

| Attribute | Type | Description | Source Script |
|-----------|------|-------------|---------------|
| `subject_id` | `str` | Subject identifier. | `src/analysis/connectivity.py` |
| `condition` | `str` | "pre" or "post". | `src/analysis/connectivity.py` |
| `matrix` | `np.ndarray` | Symmetric ROI×ROI correlation matrix (float32). | `src/analysis/connectivity.py` |
| `atlas_name` | `str` | Name of the atlas used (e.g., "Schaefer400"). | `src/analysis/connectivity.py` |
| `n_rois` | `int` | Number of ROIs. | `src/analysis/connectivity.py` |

### 3. Network Metrics

Represents topological properties of the brain network for a subject and condition.

| Attribute | Type | Description | Source Script |
|-----------|------|-------------|---------------|
| `subject_id` | `str` | Subject identifier. | `src/analysis/metrics.py` |
| `condition` | `str` | "pre" or "post". | `src/analysis/metrics.py` |
| `modularity` | `float` | Modularity value (Louvain algorithm). | `src/analysis/metrics.py` |
| `global_efficiency` | `float` | Global efficiency value. | `src/analysis/metrics.py` |
| `node_strength_mean` | `float` | Mean node strength across all ROIs. | `src/analysis/metrics.py` |
| `node_strength_std` | `float` | Standard deviation of node strength. | `src/analysis/metrics.py` |
| `node_strength` | `np.ndarray` | Array of node strength values for each ROI. | `src/analysis/metrics.py` |

### 4. Statistical Results

Represents the outcome of statistical tests.

| Attribute | Type | Description | Source Script |
|-----------|------|-------------|---------------|
| `metric_name` | `str` | Name of the metric (e.g., "modularity"). | `src/analysis/stats.py` |
| `t_statistic` | `float` | t-statistic from paired t-test. | `src/analysis/stats.py` |
| `p_value_uncorrected` | `float` | Uncorrected p-value. | `src/analysis/stats.py` |
| `p_value_fdr` | `float` | FDR-corrected p-value. | `src/analysis/stats.py` |
| `cohen_d` | `float` | Effect size (Cohen's d). | `src/analysis/stats.py` |
| `n_subjects` | `int` | Number of subjects used in the test. | `src/analysis/stats.py` |
| `permutation_p_value` | `float` | Empirical p-value from permutation testing. | `src/analysis/stats.py` |

## Data Flow

1.  **Raw Data**: Downloaded from OpenNeuro (NIfTI files). (`src/data/download.py`)
2.  **Preprocessed Data**: Motion-corrected, normalized, filtered BOLD time series (`.npy`). (`src/data/preprocess.py`)
3.  **Quality Metrics**: FD calculated from residual motion parameters. (`src/data/quality_check.py`)
4.  **Connectivity Matrices**: Correlation matrices computed from preprocessed data (`.npy`). (`src/analysis/connectivity.py`)
5.  **Network Metrics**: Metrics computed from connectivity matrices (`.csv`). (`src/analysis/metrics.py`)
6.  **Statistical Results**: Results of hypothesis tests (`.csv`). (`src/analysis/stats.py`)
7.  **Visualizations**: Plots generated from metrics and results (`.png`). (`src/viz/`)

## Storage Constraints

-   **Raw Data**: Stored temporarily during preprocessing, then deleted to save space.
-   **Preprocessed Data**: Compressed `.npy` files. Estimated size: A dataset of moderate scale for 20 subjects.
-   **Connectivity Matrices**: Compressed `.npy` files. Estimated size: ~MB for 20 subjects.
-   **Metrics & Results**: `.csv` files. Negligible size.
-   **Total Disk Usage**: < 14GB.