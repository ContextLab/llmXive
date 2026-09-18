# System Architecture

## Overview

The Plant Secondary Metabolite Prediction Pipeline is a modular, data-driven system designed to integrate genomic and metabolomic data for predictive modeling. The architecture follows a layered design pattern with clear separation of concerns.

## Architectural Principles

1. **Modularity**: Each functional component is encapsulated in its own module
2. **Schema Enforcement**: All data passes through Pydantic models for validation
3. **Reproducibility**: Checksums and timestamps track data provenance
4. **Phylogenetic Awareness**: Models account for evolutionary relationships
5. **Fail-Loud**: Errors are raised immediately rather than silently failing

## Component Layers

### 1. Data Layer (`code/data/`)

Responsible for data acquisition, preprocessing, and alignment.

**Components**:
- `download.py`: Fetches genomic and metabolite data from external sources
- `preprocess.py`: Runs antiSMASH, harmonizes metabolite data, maps BGCs to metabolites
- `align.py`: Merges genomic and metabolomic data, filters partial rows

**Data Flow**:
```
External Sources → Download → Preprocess → Align → Aligned Matrix
```

### 2. Modeling Layer (`code/modeling/`)

Implements predictive models with phylogenetic corrections.

**Components**:
- `phylo.py`: Phylogenetic tree loading, covariance matrix construction, PGLS training
- `train.py`: Model training (RF, Elastic Net, Gradient Boosting), PCA, cross-validation
- `eval.py`: Model evaluation, sensitivity analysis, baseline comparison

**Modeling Flow**:
```
Aligned Matrix → PCA → Train Models → Evaluate → Sensitivity Analysis → Report
```

### 3. Configuration Layer (`code/config*.py`)

Manages project configuration and environment variables.

**Components**:
- `config.py`: YAML-based configuration with Pydantic validation
- `config_env.py`: Environment variable management for API keys

### 4. Utility Layer (`code/utils/`)

Shared utilities for parsing, logging, and data hygiene.

**Components**:
- `anti_smash_parser.py`: JSON parsing for antiSMASH output
- `phylogeny.py`: Phylogenetic tree manipulation utilities
- `logging.py`: Centralized logging configuration
- `data_hygiene.py`: Checksum calculation and verification
- `report.py`: Report generation utilities

### 5. CLI Layer (`code/cli/`)

Command-line interface for pipeline execution.

**Components**:
- `main.py`: Entry point with argument parsing

## Data Flow Diagram

```
┌─────────────────┐
│ External Sources│
│ (NCBI, PMDB) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Download Layer │
│ (download.py) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Preprocess Layer│
│ (preprocess.py) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Align Layer │
│ (align.py) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ PCA Layer │
│ (train.py) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Modeling Layer │
│ (phylo.py, train│
│ eval.py) │
└────────┬────────┘
 │
 ▼
┌─────────────────┐
│ Report Layer │
│ (utils/report.py│
│ cli/main.py)│
└─────────────────┘
```

## Model Architecture

### Primary Model: PGLS

The Phylogenetic Generalized Least Squares model accounts for non-independence due to shared evolutionary history.

**Input**:
- BGC presence/absence matrix
- Metabolite abundance matrix (log-transformed)
- Phylogenetic covariance matrix

**Output**:
- Regression coefficients
- R² score
- Feature importance

### Secondary Models

- **Random Forest**: Non-linear relationships, feature importance
- **Elastic Net**: Regularized linear model with feature selection
- **Gradient Boosting**: Ensemble method for improved accuracy

### Baseline: Phylogenetic Permutation

Shuffles predictors and targets simultaneously while preserving phylogenetic structure to establish a null baseline.

## Configuration Architecture

### Configuration Hierarchy

1. **Environment Variables**: API keys, paths (highest priority)
2. **YAML Config File**: Model parameters, species list
3. **Defaults**: Hard-coded sensible defaults (lowest priority)

### Schema Enforcement

All configuration values pass through Pydantic models:
- `ConfigSettings`: Main configuration container
- `Species`: Species metadata
- `Metabolite`: Metabolite profile schema
- `ModelOutput`: Model result schema

## Testing Strategy

### Unit Tests

- Test individual functions with mock data
- Validate schema enforcement
- Test edge cases (zero BGCs, missing metabolites)

### Integration Tests

- End-to-end data alignment on small dataset
- Verify pipeline stages produce expected outputs

### Validation Tests

- Quickstart validation script
- CI/CD pipeline checks

## Deployment Architecture

### Local Execution

```bash
python -m code.cli.main --config config.yaml
```

### CI/CD Pipeline

1. Linting (Ruff, Flake8)
2. Formatting (Black)
3. Unit Tests
4. Integration Tests
5. Quickstart Validation

## Error Handling

### Fail-Loud Principle

- Network failures: Raise `DownloadError` immediately
- Schema violations: Raise `ValidationError` immediately
- Missing data: Raise `FileNotFoundError` immediately
- No synthetic fallbacks: Failed real fetch = failed run

### Logging

- File handlers for persistent logs
- Console handlers for real-time feedback
- Structured logging with timestamps and levels

## Security Considerations

- API keys stored in environment variables
- No credentials in code or configuration files
- `.env.example` provides template without secrets