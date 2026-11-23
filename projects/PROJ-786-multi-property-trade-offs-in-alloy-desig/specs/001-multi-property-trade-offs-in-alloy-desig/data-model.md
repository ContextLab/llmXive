# Data Model: Multi-Property Trade-Offs in Alloy Design

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/processed/` as CSV or JSON files. The `contracts/` directory contains YAML schemas for validation.

## Core Entities

### 1. AlloyEntry
Represents a single alloy composition and its properties.

**Source**: `data/processed/encoded_alloys.csv`
**Schema**: `contracts/alloy_entry.schema.yaml`

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `composition` | string | Chemical formula (e.g., "Fe0.8Ni0.2") | Non-null, unique |
| `bulk_modulus` | float | Bulk Modulus (GPa) | > 0, non-null |
| `shear_modulus` | float | Shear Modulus (GPa) | > 0, non-null |
| `elements` | list[string] | List of constituent elements | Non-empty |
| `ilr_features` | list[float] | Isometric log-ratio transformed features | Length = num_elements - 1 |
| `periodic_desc` | list[float] | Weighted periodic descriptors | Length = num_elements * 2 |
| `system_group` | string | Primary constituent group (e.g., "Fe-Ni") | Non-null |
| `valid` | bool | Filtered for non-null moduli | True |

### 2. ClusterAnalysis
Represents the result of HDBSCAN clustering and decoupling analysis.

**Source**: `data/processed/cluster_analysis.json`
**Schema**: `contracts/cluster_analysis.schema.yaml` (Implicit in CSV/JSON)

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `cluster_id` | int | Cluster identifier | >= 0 |
| `size` | int | Number of samples in cluster | > 0 |
| `correlation_coefficient` | float | Local Pearson r (K vs G) | [-1, 1] |
| `residual_variance` | float | Variance from Poisson line (if applicable) | >= 0 |
| `is_decoupled` | bool | Meets SC-002 criteria | True/False |
| `decoupling_reason` | string | "low_correlation" or "poisson_anomaly" | Enum |
| `p_value` | float | P-value from local permutation test | [0, 1] |
| `bootstrap_ci` | list[float] | 95% CI of correlation from bootstrap | [0, 1] |

### 3. ModelValidation
Represents the output of LOSO-CV and uncertainty metrics.

**Source**: `data/processed/model_validation_report.json`
**Schema**: `contracts/model_validation.schema.yaml`

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Unique identifier for the sample | Non-null |
| `predicted_bulk` | float | Predicted Bulk Modulus | Any |
| `predicted_shear` | float | Predicted Shear Modulus | Any |
| `actual_bulk` | float | Actual Bulk Modulus | > 0 |
| `actual_shear` | float | Actual Shear Modulus | > 0 |
| `uncertainty_variance` | float | Variance across LOSO-CV splits | >= 0 |
| `hull_distance` | float | Distance from convex hull centroid | >= 0 |
| `is_boundary` | bool | Within 5% of hull radius | True/False |
| `is_valid_composition` | bool | Passed simplex projection check | True |

### 4. SensitivityAnalysis
Represents the robustness of decoupling clusters to threshold changes.

**Source**: `data/processed/sensitivity_analysis.csv`
**Schema**: `contracts/sensitivity_analysis.schema.yaml`

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `threshold` | float | Correlation/Residual threshold | [0.1, 0.9] |
| `robustness_score` | float | Jaccard Index with adjacent threshold | [0, 1] |
| `num_clusters` | int | Number of clusters at this threshold | >= 0 |
| `bootstrap_ci_lower` | float | Lower bound of 95% CI | >= 0 |
| `bootstrap_ci_upper` | float | Upper bound of 95% CI | <= 1 |

## Data Flow

1. **Ingestion**: Raw OQMD CSV -> Filtered/Encoded `encoded_alloys.csv`.
2. **Feasibility**: `encoded_alloys.csv` -> `feasibility_report.json` (Global r, analysis mode).
3. **Modeling**: `encoded_alloys.csv` -> `model_validation_report.json` (Predictions, uncertainty).
4. **Clustering**: `encoded_alloys.csv` + `feasibility_report.json` -> `cluster_analysis.json`.
5. **Sensitivity**: `cluster_analysis.json` -> `sensitivity_analysis.csv`.
6. **Optimization**: `encoded_alloys.csv` -> `pareto_frontier.csv`.

## Storage Constraints

- **Format**: CSV for tabular data (efficient streaming), JSON for structured reports.
- **Encoding**: UTF-8.
- **Compression**: Raw data gzipped; processed data uncompressed for speed.
- **Checksums**: All files in `data/` must have a corresponding `.sha256` file.