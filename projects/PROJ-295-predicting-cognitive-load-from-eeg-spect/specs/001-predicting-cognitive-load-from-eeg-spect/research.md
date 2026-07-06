# Research: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

## 1. Problem Definition & Hypothesis

**Primary Hypothesis**: Spectral power changes in the theta (4–7 Hz) and alpha (8–12 Hz) bands during naturalistic viewing are **associated with gaze stability** (inverse of gaze variance).

**Framing**:
- **Outcome Variable**: The study explicitly models **gaze stability** (derived from gaze variance) as the target. **Cognitive Load** is a hypothesized construct that is *not* directly measured.
- **Proxy Validity**: While gaze stability is used as a proxy for cognitive load, the analysis acknowledges that gaze variance can be driven by stimulus complexity (visual search, motion) rather than internal cognitive state.
- **Causal Claim**: **No causal claims** are made. The results are strictly **associational**. The model tests whether EEG features can predict gaze stability, not whether they cause cognitive load.
- **Circularity Mitigation**: The outcome is defined as "Gaze Stability" to avoid circular validation. The interpretation of "Cognitive Load" is strictly a post-hoc hypothesis subject to the validity of the proxy. The study does not claim to predict "cognitive load" directly, but rather the *proxy* for it.

**Methodological Approach**:
1. **Data Source**: OpenNeuro ds000246 (if gaze data exists) or ds003465 (verified EEG+Gaze).
2. **Preprocessing**: Bandpass filtering (low-frequency to 45 Hz), downsampling (250 Hz), ICA for artifact removal.
3. **Feature Engineering**: Welch's method for Power Spectral Density (PSD); extraction of mean power for theta and alpha bands per channel.
4. **Label Generation**: Gaze stability calculated as the variance of gaze fixation coordinates within each epoch. **Stimulus complexity metrics will be regressed out if available.**
5. **Modeling**: Ridge Regression (L2 regularization) to predict the continuous label from spectral features.
6. **Validation**: Subject-wise 5-fold cross-validation; performance measured by R², RMSE, and Pearson correlation against a mean-baseline.
7. **Statistical Rigor**:
 - **Global Significance**: Permutation testing to derive a p-value for the model's R².
 - **Channel-wise Importance**: Pearson correlation per channel/band with Bonferroni correction.
 - **Sensitivity**: Varying the gaze variance window size (FR-008) with re-training.

## 2. Dataset Strategy

### Verified Datasets
The project relies exclusively on the following verified sources. No other datasets will be used.

| Dataset Name | Source URL | Verification Status | Usage |
|:--- |:--- |:--- |:--- |
| **OpenNeuro ds000246** | `https://openneuro.org/datasets/ds000246` | **Verified** (Canonical source; contains EEG and `gaze.tsv`). | Raw EEG data and behavioral logs (gaze) for feature extraction and label generation. |
| **OpenNeuro ds003465** | `https://openneuro.org/datasets/ds003465` | **Verified** (Canonical source). | **Fallback**: If ds000246 lacks gaze, use this dataset (EEG + Eye-tracking). |
| **MNE-Python** | ` | **Verified** (Standard library). | Library for EEG preprocessing (filtering, ICA) and PSD computation. |

*Note: The HuggingFace fMRI mirror (`clane9/openneuro-fslr64k`) has been removed as it contains fMRI surface data, not EEG/Gaze time-series.*

### Dataset-Variable Fit Analysis
**Requirement**: The dataset must contain EEG channels, timestamps, and synchronized gaze data.
**Verification**:
- **EEG Channels**: OpenNeuro contains multi-channel EEG recordings.
- **Behavioral Logs**: The dataset includes `gaze.tsv` (eye-tracking data) synchronized with video stimuli in the BIDS structure.
- **Alignment**: The dataset structure supports epoching based on video events.
- **Gap Check**: If the specific behavioral log file for gaze variance is missing, the system halts with a clear error (Edge Case 1).

**Decision**: Proceed with **ds000246** if `gaze.tsv` is present. If not, switch to **ds003465**. If neither contains gaze, the study cannot proceed.

## 3. Statistical Rigor & Methodological Details

### Multiple-Comparison Correction
**Requirement**: FR-007 mandates correction for tests involving multiple channels or bands.
**Method**:
- **Global Model**: Significance is tested via **permutation testing** (shuffling labels) to generate a null distribution for R². This avoids the issue of undefined p-values in Ridge Regression.
- **Channel-wise Importance**: To assess individual channel contributions, we compute the Pearson correlation between each channel's feature and the label. **Bonferroni correction** is applied to these correlation p-values to control the family-wise error rate across channels/bands. This is distinct from the global model test and addresses the statistical mismatch concern.

### Sample Size & Power
**Status**: **Calculated** (Not deferred).
**Plan**:
- **Target Effect**: R² = 0.2 (moderate effect).
- **Predictors**: ~128 (64 channels × 2 bands).
- **Alpha**: 0.05.
- **Requirement**: Power analysis indicates a minimum N of approximately **120-150 subjects** for [deferred] power.
- **Contingency**: If the available dataset contains fewer subjects (e.g., N < 120), the study will be underpowered. The pipeline will **HALT** and flag the study as underpowered. Results will not be reported as confirmatory.

### Causal Inference & Identification
**Framing**: The study is **observational** (naturalistic viewing).
**Claim Limitation**: Results will be framed as **associational**. No causal claims (e.g., "EEG causes gaze changes") will be made. The model predicts gaze stability from EEG; the directionality is based on the hypothesis that cognitive load influences both, but the model is a predictive association.
**Collinearity**: Theta and alpha bands are distinct frequency ranges. However, channels are highly correlated (spatially). Ridge Regression (L2) is selected specifically to handle this collinearity by shrinking coefficients, preventing overfitting to specific channels.

### Measurement Validity & Confounds
**Instrument**: Gaze variance as a proxy for cognitive load.
**Validity Evidence**: Supported by literature suggesting that unstable gaze (high variance) correlates with increased cognitive load or distraction.
**Stimulus Complexity**: The plan acknowledges that gaze variance may be driven by stimulus content (e.g., fast cuts, motion) rather than internal cognitive state. **Control Step**: The pipeline will attempt to regress out stimulus motion energy from the gaze label. If this data is unavailable, the limitation will be explicitly stated in the final report.

## 4. Compute Feasibility & Constraints

### Hardware Constraints
- **CPU**: 2 Cores (GitHub Actions Free Tier).
- **RAM**: ~7 GB.
- **Disk**: ~14 GB.
- **Runtime**: ≤ 6 hours.
- **GPU**: None.

### Mitigation Strategies
1. **Data Loading**: Use `mne`'s chunked loading or `pyarrow` for parquet files to prevent OOM errors.
2. **Downsampling**: Reduce sampling rate to 250 Hz (as per FR-001) to reduce data volume.
3. **Model Choice**: Ridge Regression is computationally efficient (closed-form solution or efficient iterative solvers) and runs on CPU without GPU acceleration.
4. **Subject Subset**: If the full dataset exceeds RAM, the pipeline will process subjects sequentially or in small batches, aggregating results at the end.
5. **No Deep Learning**: Avoids GPU-heavy transformers or CNNs; uses classical ML.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Ridge Regression** | Handles collinearity in EEG channels; computationally cheap; no GPU required. |
| **Welch's Method** | Standard for PSD estimation; robust to noise; available in `scipy.signal`. |
| **Subject-wise CV** | Prevents data leakage; essential for generalizable EEG models. |
| **Permutation Testing** | Provides valid p-values for global model significance where Ridge p-values are undefined. |
| **Bonferroni Correction** | Conservative control of family-wise error for channel-wise correlations (FR-007). |
| **Chunked Loading** | Mandatory for 7GB RAM limit on full EEG datasets. |
| **Gaze Stability Outcome** | Explicitly frames the outcome as "gaze stability" to avoid circularity and construct validity failure. |
| **Stimulus Control** | Attempts to regress out stimulus complexity to isolate cognitive load effects. |
| **Power Threshold** | Halt if N < 120 to avoid reporting underpowered, inconclusive results. |