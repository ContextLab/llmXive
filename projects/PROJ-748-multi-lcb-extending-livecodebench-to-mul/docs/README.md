# Multi-LCB Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Configuration](#configuration)
3. [Data Pipeline](#data-pipeline)
4. [Execution Engine](#execution-engine)
5. [Statistical Analysis](#statistical-analysis)
6. [Validation](#validation)
7. [Contributing](#contributing)

## Architecture Overview

The Multi-LCB benchmark system is designed to evaluate code generation models across multiple programming languages with rigorous statistical analysis. The architecture consists of:

- **Data Layer**: Handles dataset download, preprocessing, and contamination filtering
- **Execution Layer**: Manages sandboxed code execution with Docker containers
- **Analysis Layer**: Performs statistical modeling and correlation analysis
- **Validation Layer**: Ensures artifact integrity and schema compliance

## Configuration

All configuration is managed through `code/config.py`. Key settings include:

- **Paths**: Data, results, contracts, logs, and figures directories
- **Models**: List of LLM models to evaluate
- **Temperatures**: Sampling temperatures (0.2, 0.6, 1.0)
- **Random Seed**: For reproducibility
- **Timeout**: Execution timeout per task

Example:
```python
from code.config import get_config
config = get_config()
print(config.models)
print(config.temperatures)
```

## Data Pipeline

### Download (`code/data/download.py`)
- Fetches Multi-LCB dataset from Hugging Face
- Pins commit hash for reproducibility
- Verifies checksum integrity
- Logs task counts

### Preprocessing (`code/data/preprocess.py`)
- Converts test cases to unified format
- Applies release-date cutoffs
- Filters contaminated tasks
- Logs exclusion rates

## Execution Engine

### Sandbox (`code/execution/sandbox.py`)
- Docker-based isolated execution
- Language-specific containers (C++, Java, Rust, Python)
- Timeout handling
- Error classification

### Runner (`code/execution/runner.py`)
- LLM invocation wrapper
- Temperature and seed control
- Token usage logging
- Ten independent runs per task

### Aggregation (`code/execution/aggregators.py`)
- Computes Pass@1, Pass@5, Pass@10
- Calculates mean and standard deviation

## Statistical Analysis

### PCA (`code/analysis/pca.py`)
- Leave-One-Out PCA excluding Python
- Computes General Code Capability (PC1)

### GLMM (`code/analysis/glmm.py`)
- Generalized Linear Mixed Model fitting
- Random effects for Model and Language
- Binary pass/fail outcomes

### Correlation (`code/analysis/correlation.py`)
- Pearson correlation between Python Pass@1 and PC1
- Intra-model baseline comparison

### Correction (`code/analysis/correction.py`)
- Bonferroni correction for multiple hypothesis testing
- Significance flagging

### Sensitivity (`code/analysis/sensitivity.py`)
- Temperature variation analysis
- Variance reporting of correlation coefficients

## Validation

### Schema Validation (`code/validation/validate_artifacts.py`)
- Validates JSON artifacts against schemas
- Ensures Single Source of Truth (Constitution Principle IV)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Run `ruff` and `black` for linting/formatting
5. Submit a pull request

## License
MIT License
