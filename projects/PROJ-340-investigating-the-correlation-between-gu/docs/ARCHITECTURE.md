# Architecture Documentation

This document provides a high-level overview of the PROJ-340 pipeline architecture.

## 1. System Design

The pipeline is designed as a modular, command-line driven system. Each stage is independent and can be run separately or as part of the full orchestration.

### Components

- **Ingest (`code/ingest.py`)**: Data loading and validation.
- **Analysis (`code/analysis.py`)**: Statistical correlation.
- **Diagnostics (`code/diagnostics.py`)**: Quality checks and power analysis.
- **Report (`code/report.py`)**: Output generation and language scanning.
- **Main (`code/main.py`)**: Orchestration and error handling.

### Data Flow

1. **Input**: Raw CSV/TSV.
2. **Validation**: Schema check, outlier detection.
3. **Processing**: Filtering, transformation (CLR).
4. **Analysis**: Correlation, FDR.
5. **Diagnostics**: VIF, Power, Sensitivity.
6. **Output**: JSON, CSV, Markdown.

## 2. Technology Stack

- **Language**: Python 3.11+
- **Data Handling**: `pandas`, `numpy`
- **Statistics**: `scipy`, `statsmodels`, `scikit-learn`
- **Configuration**: `pyyaml`
- **Testing**: `pytest`

## 3. Configuration Management

- **Variables**: `data/config/required_variables.yaml`
- **Sources**: `data/config/real_data_sources.yaml`
- **State**: `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`

## 4. Error Handling

- **Fail Loudly**: The pipeline exits with code 1 on critical errors (missing data, schema mismatch).
- **Logging**: All errors are logged to `logs/` directory.
- **Validation**: Automated checks at each stage.

## 5. Scalability

- **Memory**: Current implementation loads data into memory. Streaming is planned for future versions.
- **Parallelism**: Some stages (e.g., correlation pairs) can be parallelized, but the current implementation is single-threaded for simplicity.

## 6. Security

- **Data Privacy**: No PII should be included in the dataset.
- **Access Control**: File permissions should be set appropriately.
- **Dependencies**: Regularly update dependencies to patch vulnerabilities.

## 7. Maintenance

- **Monitoring**: CI/CD pipeline monitors code quality and test coverage.
- **Updates**: Regular updates to statistical libraries and dependencies.
- **Documentation**: Keep documentation up to date with code changes.
