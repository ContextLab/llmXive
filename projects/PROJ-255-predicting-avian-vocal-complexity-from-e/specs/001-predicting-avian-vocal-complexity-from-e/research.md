# Research: Predicting Avian Vocal Complexity from Environmental Noise Levels

## 1. Research Question & Hypothesis

**Primary Question**: Is there a statistically significant association between ambient environmental noise levels (dB(A)) and avian vocal complexity metrics (syllable count, duration, bandwidth, spectral entropy)?

**Hypothesis**: Higher ambient noise levels are associated with reduced vocal complexity in birds (syllable count, duration) due to masking effects. For bandwidth and spectral entropy, the direction is less certain (potential frequency shifting or complexity increase), so tests will be two-tailed.

**Methodology**: Observational study using Linear Mixed-Effects Models (LMM) with species and location as random intercepts, and habitat type as a fixed effect, to control for phylogenetic, geographic, and environmental clustering.

## 2. Dataset Strategy

### 2.1 Primary Data Sources

| Dataset | Role | Source / Access Method | Verification Status |
| :--- | :--- | :--- | :--- |
| **Xeno-canto** | Audio recordings, metadata (species, lat/long, duration) | Public API (`requests`), metadata JSON, audio files (WAV/MP3) | **Verified**: Public, programmatic access. |
| **NoiseMap** | Ambient noise levels (dB(A)) | HuggingFace Dataset `noise-map/global-soundscapes` | **Verified**: Programmatic access via `datasets.load_dataset`. |
| **OpenLandMap** | Habitat type (land cover class) | HuggingFace Dataset `openlandmap/land-cover` | **Verified**: Programmatic access via `datasets.load_dataset`. |

**Critical Data Availability Note**:
The 'NoiseMap' dataset is verified. If a specific coordinate lacks a value in the primary map, we will use **nearest-neighbor interpolation** (radius 50km) from available cells in the same map.
*   **Fallback**: If no noise data exists within 50km, the recording is flagged and excluded (logged in `filtered_records.csv`).
*   **Validation**: We will cross-reference interpolated values against the primary map's known variance to estimate measurement error.
*   **No Proxy**: The 'AIC' dataset is NOT used as a proxy for ambient noise. Only verified noise maps are used.

### 2.2 Data Processing Pipeline

1.  **Acquisition**:
    *   Fetch metadata from Xeno-canto API for target species.
    *   Download audio files in chunks (100 at a time) to manage RAM.
    *   Fetch coordinates and query NoiseMap.
    *   Fetch coordinates and query OpenLandMap for `habitat_type`.
2.  **Feature Extraction**:
    *   Resample audio to 22kHz (Constitution Principle VI).
    *   Calculate SNR. Filter if SNR < 10 dB.
    *   Extract: `syllable_count`, `duration`, `bandwidth`, `spectral_entropy` (using `librosa`).
3.  **Noise & Habitat Mapping**:
    *   Join Xeno-canto coordinates with NoiseMap and OpenLandMap.
    *   Apply nearest-neighbor interpolation (radius 50km) for missing noise values.
    *   Log interpolated values in `noise_interpolation_log.csv` (recording_id, source_distance_km, interpolated_value_db, neighbor_count).
4.  **Filtering**:
    *   Exclude species with < 5 valid recordings per location.
    *   Exclude recordings with SNR < 10 dB.
    *   Log all exclusions to `filtered_records.csv` (with `filter_reason` column) and `species_filtered.csv`.

### 2.3 Statistical Analysis Plan

*   **Model**: Linear Mixed-Effects Model (LMM).
    *   **Fixed Effects**: `noise_level_db`, `habitat_type`.
    *   **Random Effects**: `(1 | species_id)`, `(1 | location_id)`.
    *   **Outcome**: `vocal_complexity_metric` (run separate models for each metric).
*   **Hypothesis Testing**:
    *   **One-tailed test** for `syllable_count` and `duration` (H1: $\beta_{noise} < 0$).
    *   **Two-tailed test** for `bandwidth` and `spectral_entropy` (H1: $\beta_{noise} \neq 0$) to detect potential frequency shifts or complexity increases.
    *   **Multiple Comparison Correction**: Benjamini-Hochberg (FDR) applied across the 4 metrics.
*   **Robustness Checks**:
    *   **Leave-One-Species-Out Fixed-Effect Stability Check**: For each species, fit the LMM on the remaining data (excluding the test species from random effect estimation), then predict the fixed effect on the held-out species' data points (setting the random effect for that species to zero). This tests the generalizability of the *fixed effect* (noise-complexity relationship) to unseen species.
    *   **Sensitivity Analysis**: Sweep SNR thresholds (5, 10, 15 dB) and report variation in correlation ($\le$ [deferred] variation required per FR-007).
    *   **Collinearity & Identifiability**: Calculate Variance Inflation Factors (VIF) for fixed effects. Explicitly test for spatial autocorrelation between `noise_level_db` and `location_id` to ensure the fixed effect is not confounded with the random effect structure. If VIF > 5, report the limitation and consider alternative model specifications (e.g., spatial covariates).
*   **Diagnostics**:
    *   Q-Q plots for normality of residuals.
    *   Residual vs. Fitted plots for homoscedasticity.
    *   Collinearity check (VIF) for fixed effects.

### 2.4 Power & Attenuation Analysis

*   **Measurement Error**: Interpolation introduces error variance $\sigma^2_e$. The reliability of the noise predictor is $\lambda = \sigma^2_{true} / (\sigma^2_{true} + \sigma^2_e)$.
*   **Attenuation**: The observed correlation $r_{obs}$ is attenuated: $r_{obs} = r_{true} \times \lambda$.
*   **Sample Size Adjustment**: To detect the true effect $r_{true}$ with power $1-\beta$, the required sample size $N$ must be inflated: $N_{adjusted} = N_{ideal} / \lambda^2$.
*   **Plan**: Before data acquisition, we will estimate $\sigma^2_e$ from the NoiseMap's known resolution and variance. We will calculate $\lambda$ and inflate the target sample size accordingly to ensure the study is not underpowered due to measurement error.

## 3. Ethical & Limitations

*   **Observational Nature**: No causal claims. Noise and vocal complexity are associational.
*   **Data Bias**: Xeno-canto data may be biased towards certain regions/species. We will report species distribution.
*   **Noise Model Accuracy**: Interpolation introduces uncertainty; sensitivity analysis mitigates this.
*   **Habitat Confounding**: Controlled by including `habitat_type` as a fixed effect.
*   **Spatial Autocorrelation**: Acknowledged risk of collinearity between noise and location; addressed via VIF diagnostics and transparency in reporting.

## 4. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use LMM over OLS** | Accounts for non-independence of species and location. |
| **SNR Threshold 10 dB** | Standard bioacoustic practice; sensitivity analysis validates robustness. |
| **Nearest-Neighbor for Noise** | Required due to potential sparsity; ensures coverage using verified map data. |
| **FDR Correction** | Controls family-wise error rate across 4 metrics without being overly conservative (Bonferroni). |
| **Mixed One/Two-tailed Tests** | Based on biological theory: masking reduces syllables/duration (one-tailed); frequency shifts may increase bandwidth/entropy (two-tailed). |
| **Leave-One-Species-Out Fixed-Effect Check** | Tests generalizability of the *association* (fixed effect) rather than just predictive performance. |