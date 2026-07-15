# Pipeline Workflow Documentation

## End-to-End Process Flow

This document describes the complete workflow from raw data to final report.
Each stage is modular and can be executed independently.

## Stage 1: Environment Setup

### Prerequisites
- Python 3.11+
- pip package manager
- Internet access for dataset download

### Setup Commands
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # Linux/Mac
# or
venv\Scripts\activate # Windows

# Install dependencies
pip install -r code/requirements.txt

# Verify environment
python code/check_env.py
```

### Expected Output
- Python version check: PASSED
- Package availability: PASSED
- Memory profile baseline: <6GB

## Stage 2: Data Download and Validation

### Execution
```bash
python code/download.py
```

### Process Steps
1. **Configuration Load**: Read `code/config.yaml`
2. **Primary Dataset Fetch**: Download Sleep-EDF from PhysioNet
3. **Validation**:
 - Checksum verification
 - Variable presence (EEG, pre/post fatigue)
 - Participant count (N ≥ 30)
4. **Fallback Logic**: If primary fails, attempt SHHS
5. **Output**: Raw data in `data/raw/`

### Success Criteria
- Raw files present in `data/raw/`
- No errors in `logs/pipeline.log`
- `validation_report.json` indicates success

### Failure Handling
- **Network error**: Retry with backoff, then exit
- **Checksum mismatch**: Abort with clear error
- **Missing variables**: Log to `validation_report.json`, attempt fallback
- **N < 30**: Log and attempt fallback

## Stage 3: Preprocessing

### Execution
```bash
python code/preprocess.py
```

### Process Steps
1. **Stream Loading**: Read EEG files in chunks (30-second segments)
2. **Bandpass Filtering**: 1-40 Hz using MNE-Python
3. **Artifact Rejection**:
 - Amplitude threshold: ±100 µV
 - Minimum duration: 120 seconds
4. **Logging**: Record exclusions in `logs/rejection_summary.json`
5. **Output**: Cleaned segments in `data/processed/`

### Memory Management
- **Streaming**: Files processed in chunks, not loaded entirely
- **Peak Memory**: Target <6GB
- **Chunk Size**: 30 seconds (configurable)

### Output Files
- `data/processed/cleaned_eeg/`: Filtered EEG segments
- `logs/rejection_summary.json`: Exclusion counts and reasons

### Quality Checks
- **Filter verification**: 50Hz line noise attenuated >20dB
- **Artifact rate**: Document percentage of rejected epochs
- **Duration**: Ensure segments meet 120-second minimum

## Stage 4: Feature Extraction

### Execution
```bash
python code/features.py
```

### Process Steps
1. **Load Preprocessed Data**: Read cleaned EEG segments
2. **Calculate LZC**: Per-channel Lempel-Ziv complexity
3. **Calculate PE**: Per-channel permutation entropy
4. **Aggregate**: Compute mean/SD across segments per participant
5. **Output**: CSV files with metrics

### Output Files
- `data/processed/lzc_metrics.csv`: Columns [participant_id, channel, lzc_value]
- `data/processed/pe_metrics.csv`: Columns [participant_id, channel, pe_value]

### Metric Properties
- **LZC Range**: 0.0 to 1.0 (normalized)
- **PE Range**: 0.0 to log2(order!) (typically 0.0-1.5 for order=3)
- **Missing Data**: Handled via NaN, excluded from analysis

### Performance
- **Parallelization**: Channels processed independently
- **Memory**: Streamed processing for large datasets
- **Time**: ~5-10 minutes for N=50

## Stage 5: Correlation Analysis

### Execution
```bash
python code/analysis.py
```

### Process Steps
1. **Load Metrics**: Read LZC and PE CSVs
2. **Load Fatigue Scores**: Read metadata with pre/post ratings
3. **Mode Selection**:
 - **Paired**: If pre/post data exists → delta vs delta
 - **Cross-sectional**: If only baseline → baseline vs baseline
4. **Correlation Calculation**: Spearman or Pearson
5. **FDR Correction**: Benjamini-Hochberg across channels
6. **Sensitivity Analysis**: Test p≤0.05 and p≤0.01
7. **Output**: Results in `data/analysis/`

### Output Files
- `data/analysis/correlation_results.csv`: Full correlation table
- `data/analysis/sensitivity_table.csv`: Results at multiple thresholds
- `data/analysis/validation_report.json`: If analysis mode fails

### Statistical Details
- **Method**: Spearman (default) for robustness
- **Correction**: Benjamini-Hochberg FDR
- **Thresholds**: 0.05 and 0.01
- **Effect Size**: Cohen's d reported

## Stage 6: Report Generation

### Execution
```bash
python code/report.py
```

### Process Steps
1. **Load Results**: Read correlation and sensitivity tables
2. **Calculate Effect Sizes**: Cohen's d for significant correlations
3. **Generate Report**: Markdown document with:
 - Summary statistics
 - Significant findings
 - Effect sizes
 - Limitations
 - Interpretation guidelines
4. **Output**: `data/analysis/final_report.md`

### Report Structure
```markdown
# Cognitive Fatigue Prediction Analysis Report

## Executive Summary
[Key findings and conclusions]

## Methods
- Dataset: Sleep-EDF (N=XX)
- Preprocessing: 1-40Hz bandpass, ±100µV artifact rejection
- Metrics: LZC, Permutation Entropy
- Analysis: Spearman correlation, FDR correction

## Results
### Significant Correlations
[Table of significant findings]

### Effect Sizes
[Cohen's d values]

### Sensitivity Analysis
[Robustness across thresholds]

## Discussion
- Adaptive vs. degenerative patterns
- Comparison with literature
- Limitations

## References
[Citations]
```

## Stage 7: Security and Validation

### Execution
```bash
python code/security_scan.py
```

### Process Steps
1. **Scan All Files**: Check for PII in data and logs
2. **Generate Report**: `logs/security_report.json`
3. **Fail on PII**: Exit with error if sensitive data detected

### Output
- `logs/security_report.json`: PII scan results

## Monitoring and Logging

### Log Files
- `logs/pipeline.log`: Main execution log
- `logs/rejection_summary.json`: Artifact rejection details
- `logs/security_report.json`: PII scan results

### Log Levels
- **INFO**: Progress updates, parameter values
- **WARNING**: Non-critical issues (e.g., minor data gaps)
- **ERROR**: Failures requiring attention

### Performance Monitoring
- **Memory**: Tracked via `tracemalloc`
- **Time**: Logged for each stage
- **Output**: `logs/performance_profile.json`

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependency | `pip install -r code/requirements.txt` |
| `FileNotFoundError` | Data not downloaded | Run `python code/download.py` first |
| `MemoryError` | Dataset too large | Reduce chunk size or enable streaming |
| `ValidationError` | Missing variables | Check `validation_report.json`, try fallback |
| `NetworkError` | Download failed | Check internet, retry |

### Recovery Procedures
1. **Partial Failure**: Resume from last successful stage
2. **Data Corruption**: Re-download from source
3. **Parameter Issues**: Edit `code/config.yaml` and re-run

## Parallel Execution

### Independent Stages
- **Data Download**: Can run independently
- **Preprocessing**: Depends on download completion
- **Feature Extraction**: Can run in parallel across participants
- **Analysis**: Depends on feature extraction

### Parallel Opportunities
- **Channels**: LZC/PE calculated per-channel independently
- **Participants**: Processing can be distributed across cores
- **Tests**: Unit tests for each stage run in parallel

## Reproducibility

### Seed Management
- All random operations use seeds from `code/config.yaml`
- Seeds documented in logs for full reproducibility

### Version Control
- Commit `code/config.yaml` with each run
- Document parameter changes in `docs/CHANGELOG.md`
- Tag releases with version numbers

### Environment Snapshot
- `requirements.txt` with pinned versions
- `code/check_env.py` validates environment

## Troubleshooting Guide

### Pipeline Fails at Stage 1 (Setup)
- Check Python version (must be 3.11+)
- Verify virtual environment activation
- Reinstall dependencies: `pip install -r code/requirements.txt`

### Pipeline Fails at Stage 2 (Download)
- Check internet connection
- Verify PhysioNet access
- Review `validation_report.json` for specific errors

### Pipeline Fails at Stage 3 (Preprocessing)
- Check raw data integrity
- Adjust artifact thresholds in `config.yaml`
- Review `logs/rejection_summary.json`

### Pipeline Fails at Stage 4 (Features)
- Verify preprocessed data exists
- Check for NaN values in input
- Ensure sufficient segment duration

### Pipeline Fails at Stage 5 (Analysis)
- Check metadata format (required columns)
- Verify correlation inputs are numeric
- Review `validation_report.json` for mode selection issues

### Pipeline Fails at Stage 6 (Report)
- Ensure analysis results exist
- Check for empty result sets
- Verify file permissions

## Next Steps

After successful pipeline execution:
1. Review `data/analysis/final_report.md`
2. Validate findings against literature
3. Consider sensitivity analyses
4. Prepare manuscript or presentation
5. Archive code and data for reproducibility

## Support

For issues or questions:
- Review `docs/README.md` for overview
- Check `docs/parameters.md` for configuration
- Consult `docs/interpretation_guide.md` for statistical guidance
- Examine `logs/pipeline.log` for detailed error messages