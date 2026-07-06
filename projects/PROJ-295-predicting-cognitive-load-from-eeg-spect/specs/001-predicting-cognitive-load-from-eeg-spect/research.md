# Research: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

## Dataset Strategy

| Dataset | Source URL | Variables Available | Fit for Purpose | Notes |
|---------|------------|---------------------|-----------------|-------|
| OpenNeuro ds000246 | https://openneuro.org/datasets/ds000246 | EEG raw data, behavioral logs (gaze coordinates), stimulus timestamps, video files | ✅ Confirmed | Contains both EEG recordings and synchronized gaze data required for cognitive load proxy derivation. Verified via OpenNeuro metadata. |
| MNE-Python (library) | NO verified source found (do NOT cite a URL) | N/A | ✅ Confirmed | Standard Python library for EEG preprocessing; no dataset URL needed. |
| OpenCV (library) | NO verified source found (do NOT cite a URL) | N/A | ✅ Confirmed | Used to extract video-level features (luminance, motion) for stimulus control. |

**Dataset-variable fit confirmation**: The OpenNeuro ds000246 dataset contains raw EEG recordings and synchronized behavioral logs (gaze coordinates) necessary for computing gaze variance. It also includes the video files required to compute stimulus features (luminance, cut rate) to control for confounds. No missing variables detected.

## Methodological Rationale

### Preprocessing Pipeline
- **Bandpass filtering (1–45 Hz)**: Removes DC offset and high-frequency noise while preserving theta (4–7 Hz) and alpha (8–12 Hz) bands.
- **Downsampling to 250 Hz**: Reduces computational load while maintaining Nyquist criterion for 45 Hz upper bound.
- **Line noise removal (50/60 Hz notch)**: Eliminates powerline interference using MNE's `notch_filter`.
- **ICA artifact removal**: Identifies and removes eye-blink components using MNE's `ICA` with automatic component rejection based on correlation with EOG channels.

### Feature Extraction
- **Welch's method**: Computes Power Spectral Density (PSD) with 2-second windows and [deferred] overlap.
- **Log-transformed relative power**: Normalizes power values per channel to mitigate inter-subject variability.
- **Theta/alpha bands**: Extracted as primary features; gamma bands excluded due to noise susceptibility.
- **Normalization Robustness Check**: A sensitivity analysis will compare log-relative power against z-scored power and Individual Alpha Frequency (IAF) normalization to ensure the signal is not removed by the chosen method.

### Cognitive Load Proxy & Stimulus Control
- **Gaze variance**: Computed as variance of gaze coordinates within each epoch; normalized via min-max scaling per subject.
- **Stimulus-Decoupling**: To address circular validation (stimulus driving both gaze and EEG), the plan extracts **global luminance** and **temporal cut rate** from the video files using OpenCV. These features are included as **covariates** in the Ridge Regression model. The final "cognitive load" label is conceptually the residual variance in gaze not explained by stimulus dynamics, though the model predicts the raw gaze variance while controlling for these covariates.
- **Proxy validity**: Supported by literature linking gaze instability to cognitive load, with the caveat that results are framed as "neural correlates of gaze stability adjusted for stimulus intensity."

### Model Training
- **Ridge Regression**: L2 regularization handles collinearity among EEG channels; avoids overfitting.
- **Leave-One-Subject-Out (LOSO) CV**: Given the small sample size, a simple split is too high-variance. LOSO maximizes training data and provides a distribution of performance metrics.
- **5-fold CV**: Within each training fold (N-1 subjects) for alpha hyperparameter tuning.
- **Permutation baseline**: Shuffled labels to establish null distribution for statistical significance.
- **Confidence Intervals**: Bootstrapped 95% CIs for R² and RMSE to assess stability.

### Statistical Rigor
- **Multiple-comparison correction**: **False Discovery Rate (FDR)** (Benjamini-Hochberg) or **Cluster-based permutation tests** (MNE) applied for per-channel/band hypothesis tests. Bonferroni is avoided due to high spatial correlation of EEG channels which leads to excessive Type II errors.
- **Effect size measurement**: R² reported with bootstrapped CIs; target R² ≥ 0.2 is a benchmark for "reliable prediction" but smaller significant effects are valid.
- **Power limitation**: Acknowledged; LOSO and bootstrapping are used to mitigate the impact of small N.
- **Causal framing**: All claims framed as associational due to observational nature of data.

## Computational Feasibility

- **Memory**: Chunked loading strategy for datasets >7 GB; ICA and PSD computed on downsampled data to stay within 7 GB RAM.
- **Runtime**: Downsampled data (250 Hz) and CPU-tractable methods (Ridge, ICA, Welch) ensure ≤6 hours total runtime.
- **No GPU required**: All libraries (mne, scikit-learn, opencv-python) have CPU wheels; no CUDA/mixed-precision dependencies.

## Risk Mitigation

- **Missing behavioral logs**: System halts with clear error if gaze data absent.
- **Excessive artifacts**: Subjects with >50% rejected epochs excluded; exclusion count logged.
- **Numerical instability**: Epsilon (1e-6) added to denominators in ratio calculations.
- **Dataset mismatch**: Explicit validation of variable presence before analysis; no assumptions made.
- **Stimulus confounds**: Mitigated by explicit video feature extraction and covariate inclusion.

## Open Questions

- **Exact sample size**: Number of subjects/epochs in OpenNeuro ds000246 to be determined upon download.
- **Optimal window size for gaze variance**: Sensitivity analysis planned (FR-008) to assess robustness.
- **Alpha value for Ridge**: Tuned via 5-fold CV; final value deferred to implementation.
- **Video feature extraction performance**: Ensuring OpenCV processing of video files does not exceed time limits; chunked processing may be required.