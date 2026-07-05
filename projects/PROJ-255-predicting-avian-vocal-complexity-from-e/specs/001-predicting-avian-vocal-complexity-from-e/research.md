# Research: Predicting Avian Vocal Complexity from Environmental Noise Levels

## Overview

This research phase validates the feasibility of the proposed methodology, identifies data sources, and outlines the statistical strategy for the `001-predict-avian-vocal-complexity` feature.

## Dataset Strategy

The study requires two primary data sources:
1. **Bird Vocalizations**: Metadata and audio files.
2. **Environmental Noise**: Ambient noise levels (dB(A)) mapped to geographic coordinates.

### Verified Datasets

| Dataset Name | Type | Source / URL | Status | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Xeno-canto** | Audio/Metadata | ` (API) | **Verified** | Primary source for `recording_id`, `species_id`, `lat`, `long`, `audio_url`. |
| **OpenStreetMap (OSM)** | Land-Use/Noise Proxy | ` (via `osmnx`) | **Verified** | **Primary Noise Source**. Used to classify land-use (Urban/Rural/Wild) and assign noise levels (60/40/30 dB). |
| **Global Soundscapes** | Noise Map | **NO verified source found** | **Unverified** | *Critical Note*: No verified URL exists for a programmatic download of the Global Soundscapes dataset in the provided block. **Dropped from plan.** |
| **NoiseProfile** | Derived | N/A | **N/A** | This entity is a derived construct. Values are assigned via OSM land-use classification. **No interpolation is performed.** |

### Data Acquisition Strategy & Gap Mitigation

**Constraint**: The spec requires cross-referencing with "Global Soundscapes". The "Verified datasets" block explicitly states: **"NoiseProfile: NO verified source found (do NOT cite a URL for it)."**

**Mitigation Plan**:
1. **Primary Source**: Use **OpenStreetMap (OSM)** via the `osmnx` library.
 * Query land-use tags (e.g., `landuse=residential`, `landuse=forest`) at recording coordinates.
 * Assign noise levels: Urban (dB), Rural (low), Wild (30 dB).
 * This provides a verified, programmatic source for noise estimation.
2. **Fallback (Drop Missing)**:
 * If OSM data is missing for a coordinate, **drop the record**.
 * **Gate**: If >10% of records are dropped due to missing OSM data, the pipeline **HALTS** (Task 0.4).
 * **No Interpolation**: The 50km nearest-neighbor interpolation fallback is **removed** to avoid spatial autocorrelation and measurement error (Methodology Concern).
3. **Validation**:
 * Verify that all retained records have valid OSM noise proxies.
 * Log all dropped records in `data/interim/dropped_records.csv`.

### Variable Fit Check

* **Required**: `recording_id`, `species_id`, `lat`, `long`, `audio_file`, `noise_level_db`, `syllable_count`, `duration`, `bandwidth`, `entropy`.
* **Source**: Xeno-canto provides `recording_id`, `species_id`, `lat`, `long`, `audio_file`.
* **Gap**: `noise_level_db` is not in Xeno-canto. It is derived from OSM land-use.
* **Gap**: Vocal metrics (`syllable_count`, etc.) are not in Xeno-canto metadata; they must be extracted from audio.
* **Conclusion**: The dataset strategy is **viable** provided OSM data is available. The lack of a direct "Global Soundscapes" URL is handled by switching to OSM as the primary source.

## Statistical Methodology

### Model Specification

* **Model Type**: Linear Mixed-Effects Model (LME).
* **Fixed Effect**: `noise_level_db` (continuous, derived from OSM).
* **Random Effects**: `species_id` (intercept), `location_id` (intercept).
* **Outcome Variables**: `syllable_count`, `duration_seconds`, `frequency_bandwidth_hz`, `spectral_entropy`.
* **Confounding Mitigation**: Include OSM land-use category as a fixed effect proxy to reduce bias from unmeasured habitat confounders.
* **Hypothesis**: Higher noise levels are associated with increased vocal complexity (positive coefficient) OR decreased complexity (negative coefficient), depending on the Lombard effect vs. masking hypothesis. The spec implies testing for a negative coefficient direction (one-tailed) in US-2, but the plan will support two-tailed testing with correction.

### Rigor & Corrections

1. **Multiple Comparisons**:
 * Four distinct metrics are tested (syllable, duration, bandwidth, entropy).
 * **Method**: Benjamini-Hochberg (FDR) correction to control false discovery rate, or Bonferroni if family-wise error is prioritized. The plan will implement FDR as it is more powerful for exploratory bioacoustic studies.
 * **Reference**: US-2, SC-001.

2. **Power & Sample Size**:
 * **Target**: ≥50 species (SC-004).
 * **Power Analysis**: Use `statsmodels.stats.power` to calculate minimum detectable effect size for N=50 species.
 * **Limitation**: If power < 0.8, the study will explicitly acknowledge this limitation and report effect sizes with confidence intervals rather than relying solely on p-values.

3. **Causal Inference**:
 * **Assumption**: Observational data.
 * **Framing**: All results will be described as **associational**. No claim of "noise causes X" will be made. Confounding variables (e.g., habitat type, time of day) are partially controlled via OSM land-use proxies; residual confounding is acknowledged as a limitation.

4. **Collinearity**:
 * **Risk**: Species identity and noise level might be correlated (e.g., specific species only recorded in cities).
 * **Mitigation**: Species is a random effect, not a fixed predictor. This accounts for species-specific baselines without claiming an independent "species effect" vs. "noise effect" in a collinear fixed-effects model.

5. **Measurement Validity**:
 * **Metrics**: `librosa` extraction of syllable count and entropy.
 * **Validity**: Validated against standard bioacoustic practices (Assumption in Spec). Sensitivity analysis on SNR threshold (FR-007) addresses the robustness of these metrics against noise contamination.
 * **Circularity Check**: Ensure `noise_level_db` (from OSM) is independent of `snr_db` (from audio). The SNR filter is applied for data quality, not as part of the predictor calculation.

6. **Spatial Autocorrelation**:
 * **Risk**: OSM land-use and noise levels are spatially correlated.
 * **Mitigation**: Use `location_id` as a random effect to account for spatial clustering. The noise predictor is a static, pre-computed layer (OSM) and is not re-interpolated during cross-validation, ensuring independence.

## Compute Feasibility & Constraints

* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Audio Processing**:
 * **Strategy**: Process audio in chunks. Do not load all audio into memory simultaneously.
 * **Resampling**: Downsample all audio to a standard sampling rate appropriate for bioacoustics to reduce file size and compute time.
 * **Libraries**: `librosa` (CPU-only), `scipy` for I/O.
* **Modeling**:
 * **Library**: `statsmodels` (MixedLM) or `linearmodels`. Both are CPU-tractable.
 * **LOSO CV**: Iterative fitting. With ~50 species, 50 iterations is computationally feasible (<1 hour).
* **Storage**:
 * Raw audio: Estimated to require substantial storage for 500 recordings (compressed WAV/MP3).
 * Processed data: <100 MB.
 * **Action**: Use `data/interim` for intermediate CSVs to avoid re-extracting features.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use OSM Land-Use for Noise** | Global Soundscapes is unverified; OSM provides a verified, programmatic source. |
| **Drop Missing Data (No Interpolation)** | Interpolation introduces spatial autocorrelation and measurement error (Methodology Concern). |
| **FDR Correction** | More appropriate for 4 correlated metrics than strict Bonferroni, preserving power. |
| **LOSO CV** | Essential to prevent species-level data leakage in observational data. |
| **22kHz Resampling** | Balances feature extraction quality with CPU/memory constraints on CI. |
| **Static Noise Predictor** | Ensures LOSO CV does not leak spatial information from training to test sets. |
| **Power Analysis** | Required to assess validity of N=50 species target. |
| **OSM Land-Use as Proxy** | Used to control for habitat confounding (urban vs. rural vs. wild). |