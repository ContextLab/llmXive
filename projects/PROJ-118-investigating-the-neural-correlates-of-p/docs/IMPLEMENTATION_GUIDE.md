# Implementation Guide: PROJ-118

This document details the implementation specifics for the MMN investigation pipeline.

## Data Source

- **Dataset**: OpenNeuro `ds003645`
- **Content**: Auditory oddball EEG data.
- **Acquisition**: Handled by `code/download.py` using `wget`/`curl` with retry logic.

## Preprocessing Details (User Story 1)

1. **Channel Selection**: Subsample to standard 32-channel montage (Fz, FCz, Cz, Pz, etc.) as defined in `code/preprocess.py`.
2. **Filtering**: Bandpass filter 1-30Hz. Re-reference to common average.
3. **Epoching**:
 - Baseline: Pre-stimulus.
 - Window: Pre-stimulus to post-stimulus.
 - Conditions: "standard", "deviant".
 - Output: `data/processed/epo_raw.fif`.
4. **ICA**:
 - Run ICA on raw epochs.
 - Detect components correlating >0.8 with frontal channels or showing frontal topography.
 - Remove blink components.
 - Output: `data/processed/epo_clean.fif`.
5. **Rejection**: Exclude participants with >50% rejected trials. Log to `data/processed/rejected_participants.log`.

## Metric Extraction (User Story 2)

1. **Average ERPs**: Compute separate ERPs for "standard" and "deviant" conditions.
2. **Difference Wave**: `Deviant ERP - Standard ERP`.
3. **Peak Detection**:
 - Primary Window: Early post-stimulus (approx. 100-250ms) at Fz/FCz.
 - Fallback: 100-300ms if primary fails.
 - Flag: `peak_detected` (boolean).
4. **SNR**: Calculate Signal-to-Noise Ratio for detected peaks.
5. **Output**: `results/metrics.csv` with columns: `participant_id`, `standard_amplitude`, `standard_latency`, `deviant_amplitude`, `deviant_latency`, `peak_detected`, `snr`.

## Statistical Analysis (User Story 3)

1. **Filtering**: Remove participants with `peak_detected=false` or in exclusion list.
2. **Tests**:
 - Paired t-test (or Wilcoxon) on difference scores.
 - FDR correction for 4 comparisons (Amplitude Fz, Amplitude FCz, Latency Fz, Latency FCz).
 - Mixed-effects model (`condition` fixed, `subject` random).
 - Cluster-based permutation test (1000 permutations).
3. **Effect Size**: Cohen's d with confidence intervals.
4. **Prevalence**: Proportion of participants with valid peaks.
5. **Output**: `results/statistics.json`.

## Visualization (User Story 3)

1. **ERP Plot**: Grand-average Standard, Deviant, and Difference waves with confidence intervals.
2. **Topomap**: MMN difference at peak latency.
3. **Output**: `results/plots/erp_plot.png`, `results/plots/topomap.png`.

## Dependencies

- `mne`: EEG processing.
- `numpy`, `scipy`, `pandas`: Data manipulation.
- `scikit-learn`, `pingouin`: Statistics.
- `matplotlib`: Visualization.

## Execution Constraints

- **CPU**: Dual-core.
- **RAM**: ~7 GB.
- **Disk**: ~14 GB.
- **Time**: ICA and permutation tests optimized to run within 6 hours.

## Troubleshooting

- **Missing Data**: Ensure `OPENNEURO_API_KEY` is set and `code/download.py` completes successfully.
- **Memory Errors**: Reduce ICA components or use streaming if available (currently fixed to 32 channels).
- **No Peaks**: Check `results/metrics.csv` for `peak_detected=false` flags; verify preprocessing steps.
