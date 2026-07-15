# Pipeline Parameters Reference

This document provides a complete reference for all configurable parameters in the cognitive fatigue prediction pipeline.

## Configuration File: `code/config.yaml`

```yaml
# ============================================
# SIGNAL PROCESSING PARAMETERS
# ============================================
signal_processing:
 # Bandpass filter configuration (Hz)
 filter:
 low_cutoff: 1.0 # Remove slow drifts and DC offset
 high_cutoff: 40.0 # Remove muscle artifact and line noise harmonics
 filter_type: "butter" # Butterworth filter
 order: 4 # Filter order (higher = steeper roll-off)

 # Resampling configuration
 resampling:
 target_srate: 128 # Target sampling rate in Hz
 method: "polyphase" # Resampling method

 # Artifact rejection thresholds
 artifact:
 amplitude_threshold_uv: 100 # Microvolts peak-to-peak
 min_segment_seconds: 120 # Minimum continuous segment length
 line_noise_freq: 50 # Line noise frequency (Hz)

# ============================================
# COMPLEXITY METRIC PARAMETERS
# ============================================
complexity_metrics:
 # Lempel-Ziv Complexity settings
 lzc:
 binary_threshold: "median" # Thresholding method: "median" or "mean"
 window_size_sec: 2.0 # Window size for local complexity
 overlap_sec: 0.0 # Overlap between windows

 # Permutation Entropy settings
 permutation_entropy:
 embedding_order: 3 # Number of points in pattern (m)
 time_delay: 1 # Time delay for embedding (τ)
 window_size_sec: 2.0 # Window size for local entropy
 overlap_sec: 0.0 # Overlap between windows

# ============================================
# STATISTICAL ANALYSIS PARAMETERS
# ============================================
analysis:
 # Correlation settings
 correlation:
 method: "auto" # "pearson", "spearman", or "auto"
 auto_method_threshold: 0.05 # Shapiro-Wilk p-value threshold for normality

 # Multiple comparison correction
 multiple_comparison:
 method: "benjamini_hochberg" # Correction method
 fdr_threshold: 0.05 # False discovery rate threshold

 # Sensitivity analysis thresholds
 sensitivity:
 thresholds: [0.05, 0.01] # p-value thresholds for sensitivity analysis

 # Collinearity diagnostics
 collinearity:
 vif_threshold: 5.0 # Variance Inflation Factor threshold

# ============================================
# DATASET CONFIGURATION
# ============================================
datasets:
 primary:
 name: "sleep-edf"
 physionet_id: "sleep-edf"
 version: "2.0.0"
 required_variables:
 - "pre_fatigue"
 - "post_fatigue"
 - "eeg_ch_fpz_cz"
 - "eeg_ch_pz_oz"

 fallback:
 name: "shhs"
 physionet_id: "shhs"
 version: "1.0.0"
 required_variables:
 - "ess_score"
 - "eeg_ch_c3_m2"
 - "eeg_ch_c4_m1"

 validation:
 min_participants: 30 # Minimum N for valid results
 require_paired: true # Require both pre and post measures

# ============================================
# RANDOM SEEDS
# ============================================
random_seeds:
 preprocessing: 42
 feature_extraction: 42
 analysis: 42

# ============================================
# OUTPUT CONFIGURATION
# ============================================
output:
 processed_data_dir: "data/processed"
 analysis_results_dir: "data/analysis"
 figures_dir: "figures"
 log_file: "logs/pipeline.log"
 validation_report: "data/analysis/validation_report.json"
```

## Parameter Descriptions

### Signal Processing

| Parameter | Default | Description |
|-----------|---------|-------------|
| `filter.low_cutoff` | 1.0 Hz | Lower bound of bandpass filter; removes slow drifts |
| `filter.high_cutoff` | 40.0 Hz | Upper bound; removes muscle artifact and high-frequency noise |
| `filter.order` | 4 | Filter order; higher values provide steeper roll-off but may introduce more phase distortion |
| `resampling.target_srate` | 128 Hz | Target sampling rate; balances temporal resolution and computational cost |
| `artifact.amplitude_threshold_uv` | 100 µV | Peak-to-peak amplitude threshold for epoch rejection |
| `artifact.min_segment_seconds` | 120 s | Minimum length of artifact-free segment required for analysis |
| `artifact.line_noise_freq` | 50 Hz | Frequency of line noise to notch filter (60 Hz for US regions) |

### Complexity Metrics

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lzc.binary_threshold` | "median" | Method for converting continuous signal to binary sequence |
| `lzc.window_size_sec` | 2.0 s | Window size for local complexity estimation |
| `pe.embedding_order` | 3 | Number of points in permutation pattern (m); higher values increase computational cost |
| `pe.time_delay` | 1 | Time delay for phase space reconstruction (τ) |
| `pe.window_size_sec` | 2.0 s | Window size for local entropy estimation |

### Statistical Analysis

| Parameter | Default | Description |
|-----------|---------|-------------|
| `correlation.method` | "auto" | Automatically select Pearson or Spearman based on normality test |
| `correlation.auto_method_threshold` | 0.05 | Shapiro-Wilk p-value threshold for normality decision |
| `multiple_comparison.fdr_threshold` | 0.05 | False discovery rate for Benjamini-Hochberg correction |
| `collinearity.vif_threshold` | 5.0 | Maximum acceptable Variance Inflation Factor |
| `sensitivity.thresholds` | [0.05, 0.01] | P-value thresholds for sensitivity analysis |

### Dataset Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `validation.min_participants` | 30 | Minimum number of participants with complete data |
| `validation.require_paired` | true | Require both pre- and post-fatigue measures for paired analysis |

## Modifying Parameters

To change pipeline behavior:

1. Edit `code/config.yaml` with desired parameter values
2. Ensure parameter values are within valid ranges:
 - Filter cutoffs: 0.1 - 100 Hz
 - Amplitude threshold: 50 - 500 µV
 - Minimum segment: 60 - 300 seconds
 - Embedding order: 2 - 7
 - VIF threshold: 2.0 - 10.0
3. Run validation: `python code/check_env.py`
4. Execute pipeline: `python code/download.py && python code/preprocess.py && python code/features.py && python code/analysis.py`

## Parameter Sensitivity

### Critical Parameters

The following parameters have the greatest impact on results:

1. **Filter cutoffs**: Affect frequency content of complexity metrics
2. **Artifact threshold**: Determines data quality vs. sample size trade-off
3. **Window size**: Affects temporal resolution of complexity estimates
4. **VIF threshold**: Determines collinearity tolerance in multivariate models

### Recommended Ranges

For typical adult EEG data:

- Filter: 0.5-45 Hz (conservative) or 1-40 Hz (standard)
- Artifact threshold: 75-150 µV
- Window size: 1-5 seconds
- Embedding order: 3-5

## Troubleshooting Parameter Issues

### "Filter introduces phase distortion"
- Reduce filter order (try 2 or 3)
- Use zero-phase filtering (MNE-Python applies forward-backward filtering by default)

### "Too many epochs rejected"
- Increase amplitude threshold (try 120-150 µV)
- Reduce minimum segment length (try 90-100 seconds)
- Check for persistent artifacts (eye blinks, muscle tension)

### "No significant correlations"
- Verify sample size (N ≥ 30 recommended)
- Check artifact rejection rates (excessive rejection reduces power)
- Consider alternative complexity metrics or window sizes
- Review effect sizes; non-significant results may still be meaningful
