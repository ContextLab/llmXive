# Pipeline Parameters Reference

## Configuration File

All pipeline parameters are centralized in `code/config.yaml`. This document
provides detailed explanations for each parameter.

## Filtering Parameters

```yaml
filtering:
 low_cutoff: 1.0 # Hz
 high_cutoff: 40.0 # Hz
 filter_type: "bandpass"
 filter_order: 4
```

### Rationale
- **1-40 Hz Bandpass**: Standard range for cognitive EEG analysis
 - Removes slow drifts (<1 Hz) and high-frequency noise (>40 Hz)
 - Preserves delta, theta, alpha, beta, and low gamma bands
 - Aligns with established cognitive neuroscience protocols

### Tuning Considerations
- **Lower cutoff**: Increase if residual drift persists; decrease if delta activity is critical
- **Upper cutoff**: Increase if gamma-band analysis is required; decrease if muscle artifact is severe

## Artifact Rejection Parameters

```yaml
artifacts:
 amplitude_threshold_uv: 100 # microvolts
 min_segment_duration_sec: 120
 rejection_strategy: "exclude" # or "interpolate"
```

### Rationale
- **±100 µV**: Standard threshold for rejecting eye blinks, muscle artifacts, and electrode pops
 - Balances artifact removal with data retention
 - Typical resting-state EEG amplitudes: 10-50 µV [UNRESOLVED-CLAIM: c_a1be3e71 — status=not_enough_info]
- **120-second minimum**: Ensures sufficient data for stable complexity estimates
 - LZC and PE require extended segments for reliable estimation
 - Shorter segments may produce biased metrics

### Tuning Considerations
- **Stricter threshold** (e.g., 50 µV): For high-quality recordings; may exclude more data
- **Looser threshold** (e.g., 150 µV): For noisy environments; risk of artifact contamination
- **Shorter segments**: May increase N but reduce metric reliability

## Dataset Parameters

```yaml
datasets:
 primary: "sleep-edf"
 primary_url: "https://physionet.org/content/sleep-edf/"
 fallback: "shhs"
 fallback_url: ""
 min_participants: 30
```

### Rationale
- **Primary (Sleep-EDF)**: 153 subjects with EEG and fatigue ratings
 - Validated dataset with clear protocol
 - Matches study requirements for paired pre/post measures
- **Fallback (SHHS)**: Larger sample (~5,000) but may lack specific fatigue measures
- **Minimum N=30**: Statistical power for correlation analysis
 - Ensures adequate power (≥0.80) to detect medium effects (r ≥ 0.3)

### Validation Logic
1. Attempt to fetch primary dataset
2. Verify presence of required variables (EEG, pre/post fatigue)
3. Check participant count ≥ 30
4. If validation fails, attempt fallback dataset
5. If both fail, halt with detailed `validation_report.json`

## Statistical Parameters

```yaml
statistics:
 correlation_method: "spearman" # or "pearson"
 alpha_level: 0.05
 fdr_method: "benjamini-hochberg"
 sensitivity_thresholds:
 - 0.05
 - 0.01
```

### Rationale
- **Spearman correlation**: Robust to non-normality and outliers
 - Preferred for EEG metrics which often have skewed distributions
- **Alpha level 0.05**: Standard significance threshold
- **Benjamini-Hochberg FDR**: Controls false discovery rate across multiple channels
 - More powerful than Bonferroni while maintaining error control
- **Sensitivity analysis**: Tests robustness at p≤0.01

### When to Use Pearson
- Data passes normality tests (Shapiro-Wilk p > 0.05)
- Linear relationship confirmed via scatter plots
- No significant outliers (verified via Mahalanobis distance)

## Random Seed Parameters

```yaml
random_seeds:
 preprocessing: 42
 feature_extraction: 42
 analysis: 42
```

### Rationale
- **Reproducibility**: Ensures identical results across runs
- **Consistency**: Same seed across stages for coherent debugging
- **Best Practice**: Always set seeds for any stochastic operations

## Memory Management Parameters

```yaml
performance:
 max_memory_gb: 6.0
 chunk_size_seconds: 30
 streaming_enabled: true
```

### Rationale
- **6GB limit**: Targets CPU-only CI environments with constrained RAM
- **30-second chunks**: Balances memory usage with processing efficiency
- **Streaming**: Processes data in chunks rather than loading entire files

### Implementation Notes
- `preprocess.py` uses `stream_eeg_files()` generator for memory-efficient loading
- Features are computed per-chunk and aggregated incrementally
- Peak memory usage monitored via `profile_memory.py`

## Logging Parameters

```yaml
logging:
 level: "INFO"
 format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
 file: "logs/pipeline.log"
 rejection_summary: "logs/rejection_summary.json"
```

### Rationale
- **INFO level**: Captures essential progress and warnings without excessive verbosity
- **Rejection summary**: JSON file for programmatic analysis of exclusion patterns
- **Timestamps**: Enable chronological debugging and performance tracking

## Parameter Validation

The pipeline validates parameters at startup:

1. **Filter cutoffs**: Must be positive, low < high
2. **Amplitude threshold**: Must be positive
3. **Segment duration**: Must be ≥ 60 seconds
4. **Alpha level**: Must be in (0, 1)
5. **Memory limit**: Must be > 1 GB

Invalid parameters trigger immediate exit with descriptive error messages.

## Modifying Parameters

### Recommended Workflow
1. Edit `code/config.yaml`
2. Run `python code/check_env.py` to validate configuration
3. Execute pipeline on a small subset (e.g., first 5 participants)
4. Verify outputs and logs before full run

### Version Control
- Commit `config.yaml` with each experimental run
- Document parameter changes in `docs/CHANGELOG.md`
- Use descriptive comments in YAML for rationale

## Default vs. Custom Parameters

| Parameter | Default | When to Change |
|-----------|---------|----------------|
| `low_cutoff` | 1.0 Hz | If delta-band analysis required → lower to 0.5 Hz |
| `high_cutoff` | 40.0 Hz | For gamma analysis → increase to 80 Hz (with caution) |
| `amplitude_threshold` | 100 µV | For high-noise data → increase to 150 µV |
| `min_segment_duration` | 120 sec | For short recordings → decrease to 60 sec (validate metric stability) |
| `correlation_method` | "spearman" | If normality confirmed → switch to "pearson" |
| `alpha_level` | 0.05 | For exploratory analysis → 0.10; for confirmatory → 0.01 |

## Troubleshooting

### Too Many Participants Excluded
- **Symptom**: N < 30 after artifact rejection
- **Solution**: Increase `amplitude_threshold` or decrease `min_segment_duration`
- **Trade-off**: Risk of including artifact-contaminated data

### Memory Exceeded
- **Symptom**: OOM error during preprocessing
- **Solution**: Reduce `chunk_size_seconds` or increase `max_memory_gb`
- **Alternative**: Use streaming mode (default)

### No Significant Correlations
- **Symptom**: All corrected p-values > 0.05
- **Solution**: Check effect sizes; consider lowering `alpha_level` threshold for exploration
- **Caution**: Avoid p-hacking; report null results honestly

### Inconsistent Metrics Across Channels
- **Symptom**: High variance in LZC/PE across electrodes
- **Solution**: Verify preprocessing quality; check for bad channels
- **Consideration**: May reflect genuine neurophysiological differences
