# Data Model: Autocorrelation of the Möbius Function in Short Intervals

## Overview
Defines file formats, schemas, and the data flow from raw Möbius generation to final visualisations.

## Data Flow
1. **Raw Möbius array** – `data/raw/mobius_array.npy` (int8).  
2. **Window list** – generated on‑the‑fly; stored only as a CSV of start indices for reproducibility (`data/processed/window_index.csv`).  
3. **Autocorrelation statistics** – `data/processed/autocorrelation_stats.csv`.  
4. **Null distributions** – `data/processed/null_distributions.parquet` (optional full distribution).  
5. **Uniformity test** – `data/processed/uniformity_test.json`.  
6. **Figures** – PNG heatmaps in `outputs/figures/`.

## File Specifications

### 1. Möbius Array (Raw)
- **Path**: `data/raw/mobius_array.npy`  
- **Format**: NumPy binary (`.npy`).  
- **Shape**: `(10_000_000,)`  
- **Dtype**: `int8` (values limited to -1, 0, 1).  
- **Checksum**: SHA‑256 recorded in the project state file.  

### 2. Autocorrelation Statistics (Processed)
- **Path**: `data/processed/autocorrelation_stats.csv`  
- **Format**: CSV, UTF‑8.  
- **Headers** (see `contracts/mobius_stats.schema.yaml`):  
  `interval_start`, `interval_length`, `lag`, `autocorrelation`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `zero_count`, `sensitivity_flag`, `theoretical_variance`.  

### 3. Null Distribution (Optional)
- **Path**: `data/processed/null_distributions.parquet`  
- **Format**: Parquet (columnar).  
- **Columns**: `interval_start`, `interval_length`, `lag`, `perm_value` (float).  
- **Note**: If disk space becomes tight, only the quantiles are retained in the CSV; the full Parquet file may be omitted without breaking downstream validation.

### 4. Uniformity Test Result
- **Path**: `data/processed/uniformity_test.json`  
- **Format**: JSON.  
- **Fields**: `ks_statistic` (float), `ks_pvalue` (float).  

### 5. Heatmap Figures
- **Path pattern**: `outputs/figures/heatmap_L{L}.png` where `{L}` ∈ {1000, 10000, 100000}.  
- **Resolution**: ≥ 1200 × 1200 px, PNG, RGB.  

## Data Dictionary

| Column | Type | Description |
|--------|------|-------------|
| `interval_start` | integer ≥ 1 | Starting index k of the window in the Möbius sequence. |
| `interval_length` | integer ∈ {1000, 10000, 100000} | Length L of the window. |
| `lag` | integer, 1 ≤ lag ≤ L/2 | Autocorrelation lag h. |
| `autocorrelation` | float ∈ [-1, 1] | Observed normalized autocorrelation. |
| `p_value` | float ∈ [0, 1] | Two‑sided permutation p‑value. |
| `adjusted_p_value` | float ∈ [0, 1] | BH‑adjusted p‑value. |
| `ci_lower` | float ∈ [-1, 1] | 2.5 % quantile of null distribution. |
| `ci_upper` | float ∈ [-1, 1] | 97.5 % quantile of null distribution. |
| `zero_count` | integer ≥ 0 | Number of zeros in the window. |
| `sensitivity_flag` | string ∈ {"stable","sensitive","not_applicable"} | Outcome of the zero‑density sensitivity analysis. |
| `theoretical_variance` | float ≥ 0 | Variance predicted by the PNT‑based model. |

## Integrity Constraints
- **Möbius values**: All entries in `mobius_array.npy` must be -1, 0, or 1.  
- **Lag range**: `lag` ≤ `interval_length` / 2.  
- **Probability bounds**: `p_value`, `adjusted_p_value` ∈ [0, 1].  
- **Checksum**: `mobius_array.npy` checksum must match the recorded hash.  

---
