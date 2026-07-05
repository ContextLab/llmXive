# Pipeline Parameters Documentation

This document describes the configurable parameters for the cognitive fatigue prediction pipeline.
All parameters are defined in `code/config.yaml` and can be overridden via command-line arguments
or environment variables where supported.

## Filter Configuration

### Bandpass Filter (FR-002)
- **Lower Cutoff**: 1 Hz
 - Removes slow drifts and DC offsets.
- **Upper Cutoff**: 40 Hz
 - Removes high-frequency muscle noise and line noise harmonics.
- **Filter Type**: FIR (Finite Impulse Response) via `mne.filter.filter_data`
- **Transition Band**: 0.5 Hz (default MNE behavior)

## Artifact Rejection (FR-002)

### Amplitude Threshold
- **Threshold**: ±100 µV
 - Any epoch where the peak-to-peak amplitude exceeds this range is rejected.
 - Applied channel-wise.
- **Minimum Segment Duration**: 120 seconds
 - Segments shorter than this are excluded from analysis (Edge Cases).

## Complexity Calculation Parameters

### Lempel-Ziv Complexity (LZC)
- **Binarization Method**: Median-based
 - Signal values above the median are mapped to 1, below to 0.
- **Normalization**: By sequence length (standard LZC).

### Permutation Entropy (PE)
- **Embedding Dimension (m)**: 3
 - Number of points in the time-delayed vector.
- **Time Delay (τ)**: 1
 - Lag between elements in the vector.

## Statistical Analysis Parameters

### Correlation Thresholds
- **Alpha Level**: 0.05
 - Standard significance threshold.
- **Correction Method**: Benjamini-Hochberg (FR-005)
 - Applied across all electrode comparisons to control False Discovery Rate (FDR).

### Sensitivity Analysis (FR-006)
- **Thresholds**: p ≤ 0.05, p ≤ 0.01
- **Effect Size Metric**: Pearson's r or Spearman's ρ (depending on normality).

## Data Source Configuration
- **Primary Dataset**: Sleep-EDF (PhysioNet ID: `sleep-edf`)
- **Fallback Dataset**: SHHS (Sleep Heart Health Study)
- **Minimum N**: 30 participants required for valid statistical power.
