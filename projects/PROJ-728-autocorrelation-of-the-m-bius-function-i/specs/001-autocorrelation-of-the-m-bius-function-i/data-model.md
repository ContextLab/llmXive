# Data Model: Autocorrelation of the Möbius Function in Short Intervals

## Overview
This document defines the file formats, schemas, and data flow from raw Möbius generation to final visualizations. All artifacts are immutable once written; any transformation creates a new file and records a SHA‑256 checksum in `data/checksums/manifest.sha256`.

## Data Flow Diagram
1. **Möbius Generation** – `code/sieve.py` → `data/raw/mobius_array.npy` (int8) & `data/raw/mobius_2bit.npy` (2‑bit packed).  
2. **Window Sampling** – `code/window.py` → `data/processed/window_index.csv`.  
3. **Demo Autocorrelation** – `code/demo_autocorr.py` → `data/processed/demo_autocorr.csv`.  
4. **Raw Autocorrelation** – `code/autocorrelation.py` → **`data/processed/autocorrelation_raw.csv`**.  
5. **Cross‑validation** – `code/cross_validate_autocorrelation.py` → status flag in `pipeline_status.json`.  
6. **Permutation Null** – `code/permutation.py` → adds `p_value`, `ci_lower`, `ci_upper` to `autocorrelation_stats.csv`.  
7. **FDR Correction** – `code/fdr_correction.py` → adds `adjusted_p_value`.  
8. **Calibration (SC‑005)** – `code/calibration.py` → `data/processed/calibration_test.json`.  
9. **Empirical Uniformity** – same script → `data/processed/empirical_uniformity.json`.  
10. **Sensitivity (FR‑007)** – `code/sensitivity.py` → `data/processed/sensitivity_summary.csv`.  
11. **Visualization** – `code/viz.py` → `outputs/figures/heatmap_L{L}.png`.  
12. **Checksum Manifest** – `code/checksum.py` → `data/checksums/manifest.sha256`.  

## File Specifications

### 1. Möbius Arrays (Raw)
| Path | Description | Format | Size | Notes |
|------|-------------|--------|------|-------|
| `data/raw/mobius_array.npy` | Int8 working copy of μ(n) | NumPy binary (`dtype=int8`) | ≈ 10 MB | Values ∈ {−1,0,1}. |
| `data/raw/mobius_2bit.npy` | 2‑bit packed ternary representation | NumPy binary (`dtype=uint8`) | ≈ 2.5 MB | Two entries per byte, little‑endian nibble order: first code → neutral ternary value, second code → +1, third code → −1. |

Both files are immutable after creation; their SHA‑256 hashes are recorded in `manifest.sha256`.

### 2. Window Index
- **Path**: `data/processed/window_index.csv`  
- **Columns**: `interval_start` (int ≥ 1), `interval_length` (enum {1000,10000,100000}), `window_id` (int)  
- **Row count**: 300 (100 windows × 3 lengths)  
- **Determinism**: generated with `seed=20231017`; exact start indices are reproducible.

### 3. Demo Autocorrelation (US‑1 test)
- **Path**: `data/processed/demo_autocorr.csv`  
- **Columns**: `interval_start`, `interval_length`, `lag`, `autocorrelation`  
- **Single row**: first window (start = 1, length = 1000, lag = 1).  
- **Precision**: ≥ 6 decimal places; value must match hand‑computed reference (−0.047047047047) within 1e‑9.

### 4. Raw Autocorrelation
- **Path**: `data/processed/autocorrelation_raw.csv`  
- **Columns**: `interval_start`, `interval_length`, `lag`, `autocorrelation`, `zero_count`  
- **Row count**: Σₗ 100·⌊L/2⌋ ≈ 5.55 M.  
- **Purpose**: intermediate artifact used by the permutation stage; not part of the final public CSV.

### 5. Final Statistics
- **Path**: `data/processed/autocorrelation_stats.csv`  
- **Schema**: `contracts/mobius_stats.schema.yaml` (see contract file).  
- **Columns** (in order): `interval_start`, `interval_length`, `lag`, `autocorrelation`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `zero_count`, `sensitivity_flag`, `theoretical_variance`.  

### 6. Calibration Test Result (SC‑005)
- **Path**: `data/processed/calibration_test.json`  
- **Fields**: `chi2_statistic` (float), `chi2_pvalue` (float), `ks_statistic` (float), `ks_pvalue` (float), `n_simulated_windows` (int).  

### 7. Empirical Uniformity (Labeled Result)
- **Path**: `data/processed/empirical_uniformity.json`  
- **Fields**: same as above, computed on the real Möbius p‑values.

### 8. Sensitivity Summary
- **Path**: `data/processed/sensitivity_summary.csv`  
- **Columns**: `interval_start`, `interval_length`, `adjustment` (enum {"+[deferred]","‑[deferred]","+[deferred]","‑[deferred]"}), `significant_change` (bool), `affected_lags` (comma‑separated list), `affected_lags_fdr_significant` (comma‑separated list).

### 9. Heatmap Figures
- **Pattern**: `outputs/figures/heatmap_L{L}.png` where L ∈ {1000, 10000, 100000}.  
- **Requirements**: PNG, resolution ≥ 1200 × 1200 px, includes (i) heatmap of autocorrelation, (ii) black dashed contour at value = 0, (iii) shaded Confidence interval (CI) band., (iv) red markers for BH‑significant cells.

### 10. Checksum Manifest
- **Path**: `data/checksums/manifest.sha256`  
- **Format**: one line per artifact: `<sha256>  <relative_path>`.  
- **All** processed and output files listed.

## Data Dictionary (CSV Columns)

| Column | Type | Description |
|--------|------|-------------|
| `interval_start` | integer ≥ 1 | Start index \(k\) of the window. |
| `interval_length` | integer | Length \(L\); allowed values 1000, 10000, 100000. |
| `lag` | integer, 1 ≤ lag ≤ L/2 | Lag \(h\). |
| `autocorrelation` | float ∈ [−1, 1] (NaN only for all‑zero windows) | Normalized sum \(\frac{1}{L-h}\sum\mu(k+i)\mu(k+i+h)\). |
| `p_value` | float ∈ (0, 1] | Two‑sided permutation p‑value (1/501 lattice). |
| `adjusted_p_value` | float ∈ (0, 1] | Benjamini–Hochberg FDR‑adjusted p‑value. |
| `ci_lower` | float ∈ [−1, 1] | 2.5th percentile of the null distribution. |
| `ci_upper` | float ∈ [−1, 1] | 97.5th percentile of the null distribution. |
| `zero_count` | integer ≥ 0 | Number of zeros in the window. |
| `sensitivity_flag` | string ∈ {`stable`,`sensitive`,`not_applicable`} | Outcome of the zero‑density sensitivity analysis. |
| `theoretical_variance` | float ≥ 0 | \(\sigma^2/L\) with \(\sigma^2=(6/\pi^2)(1-6/\pi^2)\approx0.2384\). |

## Integrity Constraints
- No duplicate `(interval_start, interval_length, lag)`.  
- `autocorrelation` ∈ [−1, 1] (or NaN for all‑zero windows).  
- `p_value` and `adjusted_p_value` > 0, ≤ 1.  
- `ci_lower` ≤ `ci_upper`.  
- `zero_count` ≤ `interval_length`.  
- All raw files (`*.npy`) are read‑only after creation; any modification must create a new file and update the manifest.

## Notes on the Subset‑Window Permutation Strategy

The permutation null distribution is **constructed from A suitable number of representative windows per interval length** (the first 20 entries in `window_index.csv`). Because the null model depends only on the zero‑density and the random‑sign assumption, this subset yields a reliable empirical distribution that can be applied to all windows of the same length. This design drastically reduces CPU load while preserving statistical validity (see the “Statistical Methodology” section of `research.md`). The pipeline uses **A substantial number of permutations per selected window** to achieve a p‑value resolution of a fine‑grained magnitude.  
