# Data Model: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

## 1. Overview

This document describes the data structures used in the pipeline, focusing on the transformation from raw fMRI data (and synthetic stimuli) to final regression results.

## 2. Entities

### 2.1. Stimulus Complexity Record
Represents a single timepoint (TR) with computed complexity metrics and HRF-convolved scores.

| Attribute | Type | Description |
|-----------|------|-------------|
| `tr_index` | int | Timepoint index (TR index). |
| `entropy_regressor` | float | HRF-convolved Shannon entropy value at this TR. |
| `fractal_regressor` | float | HRF-convolved fractal dimension value at this TR. |
| `luminance_regressor` | float | HRF-convolved luminance value (covariate). |
| `contrast_regressor` | float | HRF-convolved contrast value (covariate). |
| `is_synthetic` | bool | Flag indicating if the source image was synthetic (True) or raw (False). |

### 2.2. PFC Time-Series
Represents the aggregated BOLD signal for the DLPFC region.

| Attribute | Type | Description |
|-----------|------|-------------|
| `timepoint` | int | Timepoint index (TR index). |
| `bold_signal_mean` | float | Mean BOLD signal in DLPFC at this timepoint. |
| `subject_id` | str | Subject identifier. |

### 2.3. Regression Result
Represents the statistical output for a single subject or group-level analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `correlation_coefficient` | float | Pearson's r. |
| `p_value` | float | Raw p-value. |
| `fdr_corrected_p` | float | FDR-corrected p-value. |
| `permutation_p` | float | p-value from permutation test. |
| `is_significant` | bool | True if p < 0.05 (after correction). |

## 3. File Formats

### 3.1. `data/interim/complexity_metrics.csv`
- **Delimiter**: `,`
- **Columns**: `tr_index`, `entropy_regressor`, `fractal_regressor`, `luminance_regressor`, `contrast_regressor`, `is_synthetic`
- **Encoding**: UTF-8
- **Note**: One row per TR. The HRF convolution produces a time-series aligned with the BOLD TRs. The `is_synthetic` flag indicates if the source was generated.

### 3.2. `data/interim/pfc_timeseries.csv`
- **Delimiter**: `,`
- **Columns**: `timepoint`, `bold_signal_mean`, `subject_id`
- **Encoding**: UTF-8

### 3.3. `data/processed/results.json`
- **Format**: JSON array of `RegressionResult` objects.
- **Structure**:
```json
[
  {
    "subject_id": "sub-01",
    "entropy": {
      "correlation_coefficient": 0.12,
      "p_value": 0.04,
      "fdr_corrected_p": 0.08,
      "permutation_p": 0.03,
      "is_significant": true
    },
    "fractal": {
      "correlation_coefficient": -0.05,
      "p_value": 0.35,
      "fdr_corrected_p": 0.35,
      "permutation_p": 0.40,
      "is_significant": false
    }
  }
]
```

## 4. Data Lineage

1. **Raw**: OpenNeuro BOLD data + stimulus logs (`.nii.gz`, `.tsv`).
2. **Synthetic (if triggered)**: Generated naturalistic images (`.png`) via `code/synthetic_stimuli.py`.
3. **Interim**: 
   - `complexity_metrics.csv` (derived from stimulus images [raw or synthetic] + HRF convolution).
   - `pfc_timeseries.csv` (derived from BOLD data + AAL mask).
4. **Processed**: `results.json` (derived from interim CSVs via regression).

## 5. Constraints

- **Memory**: `complexity_metrics.csv` must be written in chunks to avoid loading all frames into memory at once.
- **Integrity**: Checksums of raw data must match `data/metadata.yaml`. Synthetic generation parameters and seed must also be recorded.
- **Null Handling**: Missing frames excluded; NaNs in fractal dimension replaced with 0 or flagged.
- **Transformation Rule**: The HRF convolution produces a time-series aligned with the BOLD TRs. The CSV stores one row per TR with the scalar regressor value for that timepoint.