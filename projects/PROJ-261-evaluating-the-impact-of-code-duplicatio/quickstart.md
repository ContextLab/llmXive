# Quick Start Guide - Code Duplication Impact Analysis

## Overview

This guide provides step-by-step instructions to run the complete analysis pipeline
for evaluating the impact of code duplication on LLM code understanding.

## Prerequisites

- Python 3.11+
- pip package manager
- 7GB+ available RAM (SC-002 memory constraint)
- Internet connection for dataset download

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install -r requirements-dev.txt
```

## Running the Pipeline

### Stage 1: Download Data

Download the GitHub code dataset using streaming mode to stay within memory limits:

```bash
python code/data_loader.py --max-samples 1000
```

This will:
- Stream the `codeparrot/github-code` dataset
- Filter for Python files
- Save to `data/raw/github-code-sample.csv`
- Generate checksum for validation

### Stage 2: PII Scan

Scan all downloaded data for PII patterns:

```bash
python code/pii_scanner.py
```

### Stage 3: Compute Clone Density

Analyze code duplication using AST-based clone detection:

```bash
python code/ast_cloner.py
```

### Stage 4: Compute Perplexity

Measure model perplexity using quantized codegen model:

```bash
python code/model_metrics.py
```

### Stage 5: Run Full Pipeline

Execute the complete analysis pipeline:

```bash
python code/main.py
```

### Stage 6: Validate Results

Validate directory structure and output files:

```bash
python code/quickstart_validation.py validate_directory_structure
```

## Expected Outputs

After successful execution, the following files should exist:

- `data/raw/github-code-sample.csv` - Raw dataset samples
- `data/processed/clone_metrics.csv` - Clone density metrics
- `data/processed/perplexity_scores.csv` - Model perplexity scores
- `data/analysis/correlation_results.csv` - Correlation analysis results
- `data/analysis/figures/` - Generated visualization plots

## Troubleshooting

### Memory Issues

If you encounter memory errors, reduce the sample size:

```bash
python code/data_loader.py --max-samples 100
```

### Rate Limiting

The HuggingFace API may rate limit requests. The data loader includes automatic
retry logic with exponential backoff.

### Network Interruptions

Network errors are handled with automatic retries. If downloads fail repeatedly,
check your internet connection.

## Validation

Run the full validation suite:

```bash
# Validate directory structure
python code/quickstart_validation.py validate_directory_structure

# Validate checksums
python code/quickstart_validation.py validate_checksum_manifest

# Run all tests
pytest tests/
```

## Reproducibility

All random seeds and configuration parameters are documented in `code/config.py`.
Checksums for all artifacts are recorded in the manifest for verification.
