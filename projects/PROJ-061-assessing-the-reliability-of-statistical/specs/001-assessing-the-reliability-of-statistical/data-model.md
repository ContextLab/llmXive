# Data Model: Assessing the Reliability of Statistical Power Calculations

## Overview

This document defines the data structures used throughout the pipeline, ensuring consistency between the loader, simulation engine, and output artifacts. The model supports reproducibility, traceability of violation parameters, and validation of bootstrap reliability.

## Core Entities

### 1. Dataset Record
Represents a loaded dataset and its metadata.

| Field | Type | Description |
| :--- | :--- | :--- |
| `source` | `str` | Origin (e.g., "UCI", "OpenML"). |
| `name` | `str` | Unique identifier (e.g., "wine-quality-red"). |
| `outcome_type` | `str` | "continuous", "count", or "binary". |
| `sample_size` | `int` | Total number of rows (N). |
| `missing_rate` | `float` | Proportion of missing values (0.0 - 1.0). |
| `checksum` | `str` | SHA-256 hash of the raw file. |
| `outcome_var` | `str` | Name of the outcome variable. |
| `grouping_var` | `str` | Name of the grouping variable (or "synthetic" if shifted). |
| `grouping_definition` | `str` | Specific description of the split used for multi-class data (e.g., "Setosa vs Rest"). |

### 2. ViolationConfig
Defines the parameters for induced assumption violations.

| Field | Type | Description |
| :--- | :--- | :--- |
| `type` | `str` | "heavy_tail", "autocorrelation", "heterogeneity", "none". |
| `parameter` | `float` | Magnitude (e.g., df for t-dist, AR coefficient, mixing ratio). |
| `achieved_magnitude` | `float` | Actual measured magnitude post-injection (FR-009). |
| `applied` | `bool` | Whether the violation was successfully applied (false if data type mismatch). |

### 3. PowerEstimate
The primary output record for each dataset and condition.

| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset_id` | `str` | Reference to the Dataset Record. |
| `violation_type` | `str` | Type of induced violation (or "none" for baseline). |
| `effect_size` | `float` | Cohen's d used (0.5 or 0.8). |
| `theoretical_power` | `float` | Result from closed-form calculation on **clean** data. |
| `empirical_power` | `float` | Result from bootstrap simulation on **perturbed** data. |
| `absolute_error` | `float` | |Theoretical - Empirical|. |
| `relative_error` | `float` | Absolute Error / Theoretical Power. |
| `bootstrap_reliability_flag` | `str` | "reliable", "unreliable", "skipped". |
| `bootstrap_cv` | `float` | Coefficient of Variation of the p-value distribution (FR-010). |
| `grouping_strategy` | `str` | "natural", "synthetic_shift", "predefined_split". |
| `grouping_definition` | `str` | Detailed description of the grouping (e.g., "Class 1 vs Class 2+3"). |
| `seed` | `int` | Random seed used for this run. |
| `iterations` | `int` | Number of bootstrap iterations (1000). |
| `achieved_magnitude` | `float` | Actual magnitude of the induced violation (e.g., AR coefficient). |
| `timestamp` | `str` | ISO 8601 timestamp of the record creation. |

## Data Flow

1. **Input**: Raw datasets (CSV/ARFF) → `loaders.py` → `Dataset Record`.
2. **Processing**: `Dataset Record` + `ViolationConfig` → `perturbations.py` → Perturbed Data.
3. **Simulation**: Perturbed Data → `power_empirical.py` (with Synthetic Shift if needed) → `PowerEstimate`.
4. **Output**: `PowerEstimate` → JSON file in `data/results/`.

## Storage Strategy

- **Raw Data**: `data/raw/{source}_{name}.csv` (checksummed).
- **Processed Data**: `data/processed/{dataset_id}_{violation_type}.csv` (derived).
- **Results**: `data/results/power_estimates.json` (list of `PowerEstimate` objects).
- **Logs**: `logs/pipeline.log` (timestamped events, warnings, errors).
