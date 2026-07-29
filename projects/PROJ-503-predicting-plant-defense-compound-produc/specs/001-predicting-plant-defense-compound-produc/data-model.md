# Data Model: Predicting Plant Defense Compound Production

## Overview

This document defines the data structures, error handling framework, and file formats required for the implementation. All artifacts must be checksummed and versioned.

## Core Entities

### 1. ExpressionMatrix
- **Type**: `pandas.DataFrame`
- **Description**: Normalized gene expression data.
- **Columns**: `gene_id`, `sample_id_1`, `sample_id_2`, ...
- **Index**: `gene_id` (string)
- **Values**: TPM or FPKM (float)
- **Constraints**: No negative values; no NaNs (imputed or dropped).
- **Attributes**: `species`, `condition`, `pathway_id`, `variance`.

### 2. MetaboliteMatrix
- **Type**: `pandas.DataFrame`
- **Description**: Log-transformed metabolite concentrations.
- **Columns**: `metabolite_id`, `sample_id_1`, `sample_id_2`, ...
- **Index**: `metabolite_id` (string)
- **Values**: Log-concentration (float)
- **Constraints**: No NaNs; values > 0 before log transform.

### 3. FeatureSet
- **Type**: `list[str]` or `pandas.Index`
- **Description**: Subset of `gene_id`s belonging to defense pathways.
- **Source**: KEGG pathway IDs (terpenoid, alkaloid, phenylpropanoid).
- **Constraint**: Must map to at least 75% of known defense genes (SC-006).

### 4. ModelArtifact
- **Type**: `dict` (serialized via `pickle` or `joblib`)
- **Description**: Trained Ridge Regression model and metrics.
- **Keys**:
  - `model`: `Ridge` object.
  - `metrics`: `dict` containing `rmse`, `pearson_r`, `p_value` (per metabolite).
  - `coefficients`: `dict` mapping `metabolite_id` to `gene_id` coefficients.
  - `timestamp`: ISO 8601 string.

## Error Handling Framework

The system uses custom exceptions to enforce strict constraints. All errors must be logged to `logs/error.log`.

| Error Code | Exception Class | Condition | Action |
|------------|-----------------|-----------|--------|
| `E-DATASET` | `DatasetError` | Dataset download fails or checksum mismatch (<99% match). | Abort pipeline. |
| `E-PAIRING` | `PairingError` | < 95% of samples have matched expression/metabolite records. | Abort with `E-PAIRING`. |
| `E-TIMEOUT` | `TimeoutError` | CPU time > 4 hours. | Abort and log resource usage. |
| `E-POWER` | `PowerError` | Sample size insufficient for power analysis (N < 40). | Abort with `E-POWER`. |

## Logging Specifications

### 1. Data Pairing Log (`logs/data_pairing.json`)
- **Format**: JSON array of objects.
- **Schema**:
  ```json
  [
    {
      "sample_id": "GSM123456",
      "expression_source": "GSE12345",
      "metabolite_source": "ST000000",
      "reason": "no_sample_level_pair",
      "timestamp": "2026-06-24T10:00:00Z"
    }
  ]
  ```
- **Trigger**: When a sample in the expression matrix lacks a corresponding metabolite record.

### 2. Feature Filtering Log (`logs/feature_filtering.csv`)
- **Format**: CSV file.
- **Columns**: `gene_id`, `variance`, `reason`
- **Content**:
  - `gene_id`: Identifier.
  - `variance`: Float (variance value).
  - `reason`: "zero_variance" (if variance < 1e-10).

### 3. Feature Selection Summary (`logs/feature_selection_summary.csv`)
- **Format**: CSV file.
- **Columns**: `metric`, `value`, `threshold`, `status`
- **Content**:
  - `metric`: e.g., "retention_rate".
  - `value`: e.g., 0.78.
  - `threshold`: e.g., 0.75.
  - `status`: "passed" or "failed".

### 4. Edge Cases Log (`docs/edge_cases.md`)
- **Format**: Markdown table.
- **Content**:
  - Original Gene ID.
  - Substituted Gene ID (ortholog).
  - Sequence Identity (%).
  - Species.

## File Structure & Checksums

### Directory Layout
- `data/raw/`: Original downloaded files.
- `data/processed/`: Cleaned, paired, and normalized data.
- `logs/`: Runtime logs and error reports.
- `docs/`: Documentation and edge case logs.

### Checksum Utility (`code/utils/checksum.py`)
- **Function**: `verify_checksums(file_path, expected_hash)`
- **Algorithm**: SHA-256.
- **Usage**: Called after download to validate `data/raw/*`.
- **Output**: `True` if match, `False` otherwise (raises `E-DATASET` if false).

## Configuration

- **File**: `config.yaml` (to be created in Phase 1).
- **Key Parameters**:
  - `pairing_threshold`: 0.95 (FR-009).
  - `variance_threshold`: 1e-10 (FR-003).
  - `vif_threshold`: 5.0 (for diagnostics).
  - `max_runtime_hours`: 4.0 (FR-008).
  - `min_viable_n`: 40 (Power Analysis).