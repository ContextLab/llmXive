# Cleanup and Refactoring Guide

This document outlines the cleanup and refactoring procedures for the llmXive automated science pipeline.

## Overview

The cleanup module (`code/refactor/cleanup_utils.py`) provides utilities to:

- Ensure required directory structures exist
- Validate the execution environment
- Clean up temporary files
- Generate configuration reports
- Log pipeline operations

## Running Cleanup

### Basic Usage

```bash
# Run with default settings
python code/refactor/cleanup_utils.py

# Run with custom log file
python code/refactor/cleanup_utils.py --log-file logs/cleanup.log

# Skip temporary file cleanup
python code/refactor/cleanup_utils.py --no-cleanup-temp

# Generate a cleanup report
python code/refactor/cleanup_utils.py --report artifacts/cleanup_report.txt
```

### Programmatic Usage

```python
from refactor.cleanup_utils import run_cleanup, setup_pipeline_logger

# Set up logger
logger = setup_pipeline_logger("logs/cleanup.log")

# Run cleanup
results = run_cleanup(
 logger=logger,
 cleanup_temp=True,
 validate_dirs=True,
 output_report="artifacts/cleanup_report.txt"
)

# Check results
if results["success"]:
 print("Cleanup completed successfully")
else:
 print(f"Cleanup failed with {len(results['errors'])} errors")
```

## Cleanup Actions

### Directory Validation

The following directories are created if they don't exist:

- `data/raw/` - Raw downloaded data
- `data/processed/behavioral/` - Processed behavioral metrics
- `data/processed/centrality/` - Centrality metrics
- `data/processed/regression/` - Regression analysis results
- `data/processed/validation/` - Validation and permutation results
- `data/processed/logs/` - Log files
- `data/artifacts/` - Final artifacts
- `code/analysis/` - Analysis scripts
- `code/data/` - Data processing scripts
- `code/utils/` - Utility modules
- `code/refactor/` - Refactoring utilities

### Temporary File Cleanup

The following directories are scanned for temporary files:

- `tmp/`
- `temp/`
- `.tmp/`
- System temp directory under `llmxive/`

Files are removed and empty directories are cleaned up recursively.

### Environment Validation

The validator checks:

- Python version (requires 3.8+)
- Required directories exist
- Required packages are importable:
 - pandas
 - numpy
 - networkx
 - scikit-learn
 - statsmodels
 - nilearn
 - matplotlib
 - seaborn

## Configuration Validation

Configuration consistency checks include:

- Required keys (`data_dir`, `output_dir`)
- Path validity (absolute paths)
- Numeric constraints (thresholds between 0 and 1, positive integers)

## Logging

The cleanup module uses the standard Python logging framework:

- Console output: INFO level
- File output (if specified): DEBUG level
- Timestamps included in all log messages

## Best Practices

1. **Run before pipeline execution**: Validate the environment before running analysis
2. **Run after pipeline execution**: Clean up temporary files and generate reports
3. **Review logs**: Check for errors or warnings that might indicate issues
4. **Archive reports**: Save cleanup reports for reproducibility

## Troubleshooting

### Common Issues

- **Permission denied errors**: Ensure the script has write permissions for target directories
- **Missing packages**: Install required packages via `pip install -r code/requirements.txt`
- **Directory creation failures**: Check disk space and permissions

### Getting Help

If you encounter issues not covered here, check:

- The log file for detailed error messages
- The `results` dictionary returned by `run_cleanup()`
- The project's main documentation in `README.md`
