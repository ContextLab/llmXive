# Quickstart Validation Guide

This document describes the validation process for the Consciousness Bootstrapping project (PROJ-558).

## Overview

The quickstart validation script (`code/validation/quickstart_validator.py`) ensures that all required artifacts, files, and configurations are present and valid before proceeding with the full execution pipeline.

## Running Validation

```bash
# From the project root
python code/validation/quickstart_validator.py
```

### Options

- `--base-path`: Specify a custom base path for the project (optional)
- `--verbose`: Enable detailed output for troubleshooting

## Validation Checks

The validator performs the following checks:

1. **Project Structure**: Verifies that all required directories exist
2. **Required Files**: Checks for the presence of all mandatory files
3. **File Contents**: Validates that key files contain required content
4. **Python Syntax**: Ensures all Python files are syntactically correct
5. **Configuration**: Validates the project configuration settings

## Required Artifacts

The following artifacts must be present:

### Directories
- `data/raw` - Raw dataset files
- `data/processed` - Processed dataset files
- `artifacts/checkpoints` - Model checkpoints
- `artifacts/results` - Evaluation and analysis results
- `docs` - Documentation

### Configuration Files
- `code/config.py` - Project configuration
- `data/manifest.json` - Data manifest with checksums
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project metadata and tool configuration

### Source Code
- `code/models/recursive_llama.py` - Recursive model implementation
- `code/evaluation/metrics.py` - Evaluation metrics
- `code/training/train.py` - Training script
- `code/analysis/stats.py` - Statistical analysis

### Results Files
- `artifacts/results/statistical_report.json` - Statistical analysis results
- `artifacts/results/sensitivity_analysis.csv` - Sensitivity analysis data
- `artifacts/results/error_detection_calibration.json` - Error detection calibration
- `artifacts/results/memory_profile.log` - Memory profiling results

## Troubleshooting

### Common Issues

1. **Missing Directories**
 - Run the setup script or manually create the missing directories
 - Ensure proper permissions for file creation

2. **Configuration Errors**
 - Verify that `code/config.py` contains all required parameters
 - Check that `TOKEN_LIMIT`, `recursion_depth`, and other key settings are defined

3. **Syntax Errors**
 - Run `python -m py_compile <file>` to identify syntax issues
 - Use `ruff` and `black` to fix linting and formatting issues

4. **Missing Content**
 - Ensure that result files contain the required JSON structure
 - Verify that CSV files have the correct column headers

## Validation Workflow

1. **Initial Setup**: Run validation after project initialization
2. **During Development**: Run validation after implementing new features
3. **Before Execution**: Run validation before starting the full pipeline
4. **CI/CD Integration**: Include validation in continuous integration workflows

## Integration with CI/CD

To integrate validation into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Validate Project
 run: python code/validation/quickstart_validator.py --verbose
```

## Contact

For issues or questions about the validation process, refer to the project documentation or contact the development team.
