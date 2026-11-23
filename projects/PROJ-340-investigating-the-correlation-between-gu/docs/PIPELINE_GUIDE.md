# Pipeline Architecture Guide

This document details the internal architecture, data flow, and design decisions of the PROJ-340 pipeline.

## 1. Architecture Overview

The pipeline follows a modular, stage-based design:

1. **Ingestion (`code/ingest.py`)**: Handles data loading, schema validation, outlier detection, and filtering.
2. **Analysis (`code/analysis.py`)**: Performs correlation analysis with automatic method selection (Pearson, Spearman, ZINB).
3. **Diagnostics (`code/diagnostics.py`)**: Computes VIF, power analysis, and sensitivity metrics.
4. **Reporting (`code/report.py`)**: Generates human-readable reports and enforces causal language constraints.
5. **Orchestration (`code/main.py`)**: Coordinates stages, manages timeouts, and handles errors.

## 2. Data Flow

```mermaid
graph TD
 A[Raw Data] --> B(Ingest & Validate)
 B --> C{Missing Variables?}
 C -- Yes --> D[HALT: Error]
 C -- No --> E[Outlier Detection]
 E --> F[Filter Outliers]
 F --> G[Processed Data (Parquet)]
 G --> H(Analysis Engine)
 H --> I{Distribution Check}
 I -- Normal --> J[Pearson/Spearman]
 I -- Zero-Inflated --> K[ZINB/Hurdle]
 K --> L[Correlation Results]
 J --> L
 L --> M(Diagnostics)
 M --> N[VIF, Power, Sensitivity]
 N --> O(Report Generator)
 O --> P[Final Report & Causal Scan]
```

## 3. Key Components

### 3.1. Ingestion (`code/ingest.py`)
- **Schema Validation**: Checks input columns against `data/config/required_variables.yaml`.
- **Outlier Detection**: Uses IQR method (1.5x IQR). Outliers are logged to `data/results/outlier_report.json` and excluded from analysis.
- **Real Data Gate**: In `real` mode, fetches data from configured sources. Fails loudly if fetch fails.

### 3.2. Analysis (`code/analysis.py`)
- **Method Selection**:
 - Checks for compositional data (sum of abundances != 1).
 - Checks for zero-inflation (>30% zeros) or non-normality (Shapiro-Wilk).
 - Selects ZINB/Hurdle for zero-inflated, otherwise Pearson/Spearman.
- **FDR Correction**: Applies Benjamini-Hochberg correction to p-values.

### 3.3. Diagnostics (`code/diagnostics.py`)
- **Collinearity**: Calculates VIF. Flags pairs with VIF > 10.
- **Power Analysis**: Estimates required sample size for observed effect sizes.
- **Sensitivity**: Re-runs analysis at p < 0.01, 0.05, 0.10 to assess stability.

### 3.4. Reporting (`code/report.py`)
- **Causal Language Scan**: Regex scan for "causes", "leads to", "effect". Halts if found.
- **Report Draft**: Generates `report_draft.md` with statistical caveats.

## 4. Configuration

### `data/config/required_variables.yaml`
Defines the mandatory columns for predictors (taxa) and outcomes (sleep metrics).

### `data/config/real_data_sources.yaml`
Defines URLs or paths for real data. Used only in `--mode real`.

### `specs/001-gut-microbiome-sleep-architecture/contracts/`
Contains JSON/YAML schemas for inputs and outputs.

## 5. Error Handling

- **Missing Variables**: `SystemExit` with specific message.
- **Real Data Fetch Failure**: `RealDataFetchError` (no synthetic fallback).
- **Timeout**: `subprocess.run(..., timeout=...)` enforces 6-hour limit.
- **Causal Language**: `SystemExit` if detected in reports.

## 6. Extensibility

To add a new correlation method:
1. Implement the function in `code/analysis.py`.
2. Update `select_correlation_method()` logic.
3. Add unit tests in `tests/unit/test_analysis.py`.

To add a new data source:
1. Update `data/config/real_data_sources.yaml`.
2. Ensure the source schema matches `required_variables.yaml`.
