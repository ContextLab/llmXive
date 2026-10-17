# Data Model: Autocorrelation of the Möbius Function in Short Intervals

## Overview
Defines file formats, schemas, and the data flow from raw Möbius generation to final visualisations.

## Data Flow
1. **Raw Möbius array** – `data/raw/mobius_array.npy` (int8).  
2. **Window list** – generated on‑the‑fly; start indices are stored implicitly in the CSV.  
3. **Autocorrelation statistics** – `data/processed/autocorrelation_stats.csv`.  
4. **Uniformity test result** – `data/processed/uniformity_test.json`.  
5. **Figures** – PNG heatmaps in `outputs/figures/`.

## File Specifications

### 1. Möbius Array (Raw)
- **Path**: `data/raw/mobius_array.npy`  
- **Format**: NumPy binary (`.npy`).  
- **Shape**: `(10_000_000,)`  
- **Dtype**: `int8` (values limited to −1, 0, 1).  
- **Checksum**: SHA‑256 recorded in the project state file.

### 2. Autocorrelation Statistics (Processed)
- **Path**: `data/processed/autocorrelation_stats.csv`  
- **Format**: CSV, UTF‑8.  
- **Headers**: see `contracts/mobius_stats.schema.yaml`.  
- **Row count**: ≈ 2.78 million (90 windows × (500 + 5 000 + 50 000) lags) **when using the full 50‑window per L design**; this scales down proportionally if the fallback reduces windows.  
- **Uniqueness**: `(interval_start, interval_length, lag)` uniquely identifies a row.

### 3. Uniformity Test Result
- **Path**: `data/processed/uniformity_test.json`  
- **Format**: JSON.  
- **Fields**: `ks_statistic` (float), `ks_pvalue` (float).

### 4. Heatmap Figures
- **Path pattern**: `outputs/figures/heatmap_L{L}.png` where `{L}` ∈ {1000, 10000, 100000}.  
- **Resolution**: ≥ 1200 × 1200 px, PNG, RGB.  
- **Content**: Heatmap of autocorrelation values with zero‑line, confidence‑band shading, and significance markers.

## Data Dictionary (CSV Columns)

| Column | Type | Description |
|--------|------|-------------|
| `interval_start` | integer ≥ 1 | Starting index k of the window in the Möbius sequence. |
| `interval_length` | integer | Length L of the window; enum {1000, 10000, 100000}. |
| `lag` | integer, 1 ≤ lag ≤ L/2 | Autocorrelation lag h. |
| `autocorrelation` | float ∈ [−1, 1] | Observed normalized autocorrelation \(r_{k,L}(h)\). |
| `p_value` | float ∈ (0, 1] | Two-sided p‑value from the 5,000‑permutation test. |
| `adjusted_p_value` | float ∈ (0, 1] | Benjamini‑Hochberg FDR‑adjusted p‑value. |
| `ci_lower` | float ∈ [−1, 1] | 2.5th percentile of the null distribution. |
| `ci_upper` | float ∈ [−1, 1] | 97.5th percentile of the null distribution. |
| `zero_count` | integer ≥ 0 | Number of zeros in the specific window. |
| `sensitivity_flag` | string ∈ {"stable","sensitive","not_applicable"} | Result of the inline zero‑density sensitivity analysis. |
| `theoretical_variance` | float ≥ 0 | Theoretical variance under the Prime Number Theorem (PNT) assumption: σ²/L where σ² = (6/π²)(1 − 6/π²). |

## Integrity Constraints
- **Möbius values**: All entries in `mobius_array.npy` must be −1, 0, 1.  
- **Lag range**: `lag` ≤ `interval_length`/2.  
- **Probability bounds**: `p_value`, `adjusted_p_value` ∈ (0, 1].  
- **Confidence interval ordering**: `ci_lower` ≤ `ci_upper`.  
- **Checksum**: `mobius_array.npy` checksum must match the recorded hash.  
- **Uniqueness**: No duplicate `(interval_start, interval_length, lag)` rows.  

---



