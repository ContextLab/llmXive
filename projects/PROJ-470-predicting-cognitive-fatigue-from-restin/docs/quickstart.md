# Quick Start Guide

This guide provides step-by-step instructions for running the cognitive fatigue prediction pipeline from scratch.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Virtual environment tool (venv or virtualenv)
- PhysioNet account (for dataset access)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd projects/PROJ-470-predicting-cognitive-fatigue-from-restin
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

Required packages:
- `mne`: EEG processing
- `scikit-learn`: Machine learning utilities
- `numpy`, `pandas`: Numerical computing
- `lempel-ziv-complexity`: LZC calculation
- `scipy`: Scientific computing
- `pyyaml`: Configuration parsing
- `pytest`: Testing

### 4. Set Environment Variables

For PhysioNet access:

```bash
export PHYSIONET_USER="your_username"
export PHYSIONET_PASSWORD="your_password"
```

## Running the Pipeline

### Step 1: Environment Check

Verify Python version and package installation:

```bash
python code/check_env.py
```

Expected output:
```
Python version: 3.11.4 ✓
mne: 1.5.0 ✓
scikit-learn: 1.3.0 ✓
...
All checks passed.
```

### Step 2: Download Data

Fetch and validate the Sleep-EDF dataset:

```bash
python code/download.py
```

This will:
- Download raw EEG files from PhysioNet
- Validate presence of required variables
- Check participant count (N ≥ 30)
- Generate `data/analysis/validation_report.json`

**Note**: If Sleep-EDF validation fails, the pipeline will attempt to use the SHHS dataset as a fallback.

### Step 3: Preprocess Data

Apply filtering and artifact rejection:

```bash
python code/preprocess.py
```

This will:
- Apply 1-40 Hz bandpass filter
- Reject epochs exceeding ±100 µV threshold
- Exclude segments < 120 seconds
- Write processed data to `data/processed/`
- Log exclusion counts to `logs/pipeline.log`

### Step 4: Extract Features

Calculate complexity metrics:

```bash
python code/features.py
```

This will:
- Compute Lempel-Ziv complexity per channel
- Compute Permutation Entropy per channel
- Write results to:
 - `data/processed/lzc_metrics.csv`
 - `data/processed/pe_metrics.csv`

### Step 5: Run Analysis

Perform correlation analysis:

```bash
python code/analysis.py
```

This will:
- Validate metadata structure
- Select analysis mode (paired or cross-sectional)
- Compute Pearson/Spearman correlations
- Apply Benjamini-Hochberg correction
- Generate sensitivity table
- Write results to `data/analysis/`

### Step 6: Generate Report

Create final report:

```bash
python code/report.py
```

This will:
- Calculate effect sizes
- Generate statistical summary
- Write report to `data/analysis/final_report.md`

## Output Files

After successful pipeline execution:

```
data/
├── processed/
│ ├── lzc_metrics.csv # Lempel-Ziv complexity per channel
│ └── pe_metrics.csv # Permutation entropy per channel
└── analysis/
 ├── validation_report.json # Dataset validation status
 ├── correlation_results.csv # Correlation coefficients and p-values
 ├── sensitivity_table.csv # Results at multiple thresholds
 └── final_report.md # Comprehensive analysis report
```

## Troubleshooting

### "PhysioNet authentication failed"

- Verify credentials in environment variables
- Ensure data use agreement is signed on PhysioNet
- Check network connectivity

### "Validation failed: N < 30"

- Check artifact rejection thresholds (may be too strict)
- Verify fatigue ratings are present in dataset
- Consider enabling fallback dataset (SHHS)

### "Memory error during preprocessing"

- Ensure streaming is enabled in `config.yaml`
- Reduce batch size for chunked processing
- Close other applications to free memory

### "No significant correlations found"

- Check sample size (N ≥ 30 recommended)
- Verify data quality (artifact rejection rates)
- Review effect sizes; non-significant results may still be meaningful

## Performance Tips

### CPU-Only Execution

The pipeline is optimized for CPU-only execution:
- Streaming data loading reduces memory usage (<6 GB peak)
- Parallel processing is disabled for CI compatibility
- Batch processing is chunked for large datasets

### Memory Profiling

To profile memory usage:

```bash
python code/profile_memory.py
```

This will generate a memory profile report in `logs/memory_profile.json`.

## Next Steps

- Review `docs/statistical_guidelines.md` for interpretation of results
- Check `docs/pipeline_parameters.md` for configuration options
- Run `pytest tests/` to execute the test suite
- Customize parameters in `code/config.yaml` for your use case

## Support

For issues or questions:
- Check `logs/pipeline.log` for detailed error messages
- Review `docs/README.md` for comprehensive documentation
- Consult the project's GitHub issues page