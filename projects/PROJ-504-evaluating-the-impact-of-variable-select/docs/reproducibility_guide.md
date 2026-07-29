# Reproducibility Guide

## Overview

This guide ensures that all results from PROJ-504 can be exactly reproduced by re-running the pipeline with pinned seeds and verified data sources.

## Prerequisites

1. **Environment**: Python 3.9+ with exact dependency versions from `requirements.txt`
2. **Data**: All raw OpenML datasets must be present in `data/raw/` with valid checksums
3. **State**: `state/checksums.json` must exist and match current files

## Step-by-Step Reproduction

### 1. Verify Data Integrity

```bash
# Run checksum verification
python code/data/validator.py

# Expected output: All checksums match
```

### 2. Check Configuration

Ensure `code/config.py` has:
- `seed`: Same value as original run
- `openml_ids`: Same dataset IDs
- `simulations_per_condition`: Same count from T004 pilot

### 3. Re-run Data Pipeline

```bash
# Fetch and validate datasets
python code/data/downloader.py

# Generate simulations
python code/data/simulators.py
```

### 4. Re-run Analysis

```bash
# Variable selection and power calculation
python code/analysis/selectors.py
python code/analysis/metrics.py

# Statistical comparisons
python code/analysis/comparators.py
```

### 5. Generate Visualizations

```bash
python code/viz/plots.py
```

### 6. Verify Outputs

```bash
# Compare checksums of processed files
python code/utils/checksum_verifier.py

# Validate schema compliance
pytest tests/contract/test_schema.py -v
```

## Checksum Verification

All processed files should match original checksums:

```bash
# Generate current checksums
sha256sum data/processed/*.csv > current_checksums.txt

# Compare to stored checksums
diff current_checksums.txt state/checksums.json
```

## Expected Outputs

After reproduction, verify:

1. `data/processed/simulation_results.csv`: Same row count (n=24,000) and checksum
2. `results/plots/`: Same number of PNG files with identical dimensions
3. `results/final_report.md`: Same statistical test results (p-values within floating-point tolerance)
4. `results/sensitivity_report.csv`: Identical power rates at each α threshold

## Troubleshooting

### Checksum Mismatch
- Verify `requirements.txt` versions match original
- Ensure same OpenML datasets were fetched
- Check random seed is identical

### Different P-values
- Small floating-point differences (< 1e-10) are acceptable
- Large differences indicate configuration mismatch
- Verify same selection methods were used

### Missing Files
- Re-run the full pipeline from `pipeline.py`
- Check watchdog logs for early termination
- Verify resource limits weren't exceeded

## Automated Reproduction Script

A convenience script is available:

```bash
# Run full reproduction
python code/reproduce.py

# This script:
# 1. Verifies checksums
# 2. Re-runs all pipeline stages
# 3. Compares outputs to stored results
# 4. Generates a reproducibility report
```

## Version Control

To ensure exact reproduction:

1. Check out the specific git commit used for original run
2. Verify `requirements.txt` is pinned to exact versions
3. Confirm all configuration files are unchanged

## Limitations

- Network-dependent steps (OpenML fetching) require internet access
- Runtime may vary slightly due to system load
- Memory usage depends on available RAM
- Some floating-point operations may have minor precision differences across architectures
