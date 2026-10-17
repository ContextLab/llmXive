# Data Model: Autocorrelation of the Möbius Function in Short Intervals

## Overview
File formats, schemas, and data flow from raw Möbius generation to final visualizations.

## Data Flow
1. `code/sieve.py` → `data/raw/mobius_array.npy` (int8 working copy) and `data/raw/mobius_2bit.npy` (2-bit packed ternary array, FR-001) — both immutable raw artifacts.
2. Window sampling (seeded) → `data/processed/window_index.csv`.
3. `code/autocorrelation.py` (FFT + int64 cross-validation) + `code/permutation.py` → `data/processed/autocorrelation_stats.csv` (incremental checkpoints).
4. `code/sensitivity.py` → `data/processed/sensitivity_summary.csv`.
5. `code/calibration.py` → `data/processed/calibration_test.json` (SC-005, simulated null) and `data/processed/empirical_uniformity.json` (real data, labeled).
6. `code/viz.py` → `outputs/figures/heatmap_L{L}.png`.
7. `code/main.py` → `data/processed/pipeline_status.json` (per-stage success/failure record, incl. cross-check results).

## File Specifications

### 1. Möbius Arrays (Raw)
- **`data/raw/mobius_2bit.npy`** (FR-001-compliant stored artifact): NumPy binary; shape (a large one-dimensional array); dtype `uint8`; **2-bit-per-entry packed ternary encoding** (2 values per byte, little-endian nibble order; code 0→μ=0, 1→μ=1, 2→μ=−1); ~2.5 MB; SHA-256 recorded in project state file. Never modified in place.
- **`data/raw/mobius_array.npy`** (working copy): shape (large one-dimensional array); dtype `int8` (values −1, 0, 1); derived from the packed array by exact unpacking (round-trip unit-tested); ~10 MB; SHA-256 recorded. Never modified in place.

### 2. Window Index
- **Path**: `data/processed/window_index.csv`; columns `interval_start` (int ≥ 1), `interval_length` (enum {1000, 10000, 100000}), `window_id` (int). A fixed number of rows. Deterministic from seed 20231017.

### 3. Autocorrelation Statistics
- **Path**: `data/processed/autocorrelation_stats.csv`; UTF-8 CSV; schema per `contracts/mobius_stats.schema.yaml`.
- **Row count**: ≈ 5.56 M (300 windows × (500 + 5 000 + 50 000) lags).
- **Uniqueness**: `(interval_start, interval_length, lag)`.
- Values computed via float64 FFT and cross-validated against exact `int64` direct summation on a seeded random sample of ≥ 100 (window, lag) pairs per L (Constitution VI).

### 4. Sensitivity Summary
- **Path**: `data/processed/sensitivity_summary.csv`; columns: `interval_start` (int), `interval_length` (enum), `adjustment` (enum {"+[deferred]","−[deferred]","+[deferred]","−[deferred]"}), `significant_change` (bool; raw p < 0.05 criterion per FR-007), `affected_lags` (string; comma-separated lag list, empty if none), `affected_lags_fdr_significant` (string; subset of `affected_lags` that were also BH-significant, empty if none).

### 5. Calibration Test Result (SC-005)
- **Path**: `data/processed/calibration_test.json`; fields `chi2_statistic` (float), `chi2_pvalue` (float), `ks_statistic` (float), `ks_pvalue` (float), `n_simulated_windows` (int). Computed on **simulated random-sign windows** (null calibration), NOT on real μ data.

### 6. Empirical Uniformity Result (labeled research result)
- **Path**: `data/processed/empirical_uniformity.json`; fields `chi2_statistic` (float), `chi2_pvalue` (float), `ks_statistic` (float), `ks_pvalue` (float). Computed on real μ p-values; explicitly labeled as a result about the random-sign heuristic, not test validation.

### 7. Pipeline Status
- **Path**: `data/processed/pipeline_status.json`; map of stage name → {"status": "ok"|"failed"|"skipped", "elapsed_seconds": float, "error": string|null}; includes an `autocorrelation_crosscheck` entry with `n_pairs_checked` and `max_relative_error`, and a `sensitivity` entry recording any documented scope degradation (which L subsets were run).

### 8. Heatmap Figures
- **Path pattern**: `outputs/figures/heatmap_L{L}.png`, L ∈ {1000, 10000, 100000}; PNG, ≥ 1200 × 1200 px; contains: autocorrelation heatmap, black dashed contour at autocorrelation = 0, CI band panel (2.5th/97.5th null percentiles) sharing the lag axis, red significance markers where `adjusted_p_value < 0.05`.

## Data Dictionary (CSV Columns)

| Column | Type | Description |
|--------|------|-------------|
| `interval_start` | integer ≥ 1 | Starting index k of the window. |
| `interval_length` | integer | L; enum {1000, 10000, 100000}. |
| `lag` | integer, 1 ≤ lag ≤ L/2 | Lag h. |
| `autocorrelation` | float ∈ [−1, 1] or NaN | Observed normalized autocorrelation (NaN only for all-zero windows). |
| `p_value` | float ∈ (0, 1] | Two-sided permutation p-value (1,000 permutations; +1 correction). |
| `adjusted_p_value` | float ∈ (0, 1] | BH FDR-adjusted p-value. |
| `ci_lower` | float ∈ [−1, 1] | 2.5th percentile of the null distribution. |
| `ci_upper` | float ∈ [−1, 1] | 97.5th percentile of the null distribution. |
| `zero_count` | integer ≥ 0 | Zeros in the window. |
| `sensitivity_flag` | string ∈ {"stable","sensitive","not_applicable"} | Zero-density sensitivity outcome (raw p < 0.05 criterion per FR-007). |
| `theoretical_variance` | float ≥ 0 | σ²/L, σ² = (6/π²)(1 − 6/π²) ≈ 0.2384 (source: 1211.0189). |

## Integrity Constraints
- All μ values ∈ {−1, 0, 1}; 2-bit packed array unpacks exactly to the int8 array; `lag` ≤ `interval_length`/2; `p_value`, `adjusted_p_value` ∈ (0, 1]; `ci_lower` ≤ `ci_upper`; no duplicate `(interval_start, interval_length, lag)`; both raw array checksums match the recorded hashes; raw files never modified in place.