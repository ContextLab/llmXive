# PROJ-340: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Overview
This project implements a robust, reproducible pipeline to analyze the correlation between gut microbiome composition (predictors) and sleep architecture metrics (outcomes). The pipeline enforces strict data integrity checks, compositional data corrections, and causal language constraints to ensure scientific rigor.

## Key Features
- **Real-Data Enforcement**: The pipeline fails loudly if real data cannot be fetched; no synthetic fallbacks are permitted in production runs.
- **Compositional Correction**: Automatically detects compositional data and applies SparCC/SpiecEasi or CLR transformations as appropriate.
- **Outlier Handling**: IQR-based outlier detection with exclusion logging.
- **Method Selection**: Dynamic selection of correlation methods (Pearson, Spearman, ZINB/Hurdle) based on data distribution and zero-inflation.
- **Causal Language Guard**: Scans all reports for prohibited causal language (e.g., "causes", "effect") and halts on violation.
- **Power & Sensitivity Analysis**: Comprehensive reporting on statistical power and stability of findings across thresholds.

## Project Structure
```
.
├── code/ # Core pipeline logic
│ ├── ingest.py # Data loading, validation, outlier detection
│ ├── analysis.py # Correlation analysis, method selection
│ ├── diagnostics.py # Collinearity, VIF, power analysis
│ ├── report.py # Report generation, causal scanning
│ ├── generate_synthetic_data.py # Synthetic data for testing only
│ └──...
├── data/
│ ├── raw/ # Raw input data (CSV/TSV)
│ ├── processed/ # Cleaned/filtered data (Parquet)
│ ├── results/ # Analysis outputs (JSON/CSV/MD)
│ ├── metadata/ # Method logs, flags
│ └── config/ # Schema, required variables, real data sources
├── tests/ # Unit and integration tests
├── specs/ # Design documents and contracts
└── scripts/ # Verification and utility scripts
```

## Prerequisites
- Python 3.11+
- Required dependencies listed in `requirements.txt`
- Access to a real data source (configured in `data/config/real_data_sources.yaml`)

## Quickstart

### 1. Setup Environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Data Sources
Edit `data/config/real_data_sources.yaml` to point to your verified real data source URL or local path.
```yaml
real_data:
 source_url: ""
 expected_checksum: "sha256:..."
 source_type: "public_dataset"
```

### 3. Run the Pipeline (Real Data Mode)
```bash
python code/main.py --input data/raw/real_data.csv --output data/results/
```
**Note**: If `real_data_sources.yaml` points to a missing or invalid source, the pipeline will halt with a clear error. No synthetic data will be generated.

### 4. Run Synthetic Mode (Testing Only)
For local validation of the pipeline logic:
```bash
python code/generate_synthetic_data.py --output data/raw/synthetic_test_data.csv
python code/main.py --input data/raw/synthetic_test_data.csv --output data/results/
```

## Output Artifacts
Upon successful execution, the following artifacts are generated in `data/results/`:
- `correlation_results.csv`: Main correlation matrix and p-values.
- `outlier_report.json`: Details of detected outliers and exclusions.
- `power_analysis_report.json`: Statistical power assessment.
- `sensitivity_analysis.csv`: Stability of findings across p-value thresholds.
- `causal_scan_report.json`: Verification that no causal language was used.
- `report_draft.md`: Human-readable interpretation of results.

## Known Limitations
- **Compute Constraints**: Full-scale analysis on large microbiome datasets may require >6 hours; the pipeline includes a 6-hour timeout gate for CI.
- **Data Availability**: Requires a verified real data source. If none is available, the pipeline will fail with `RealDataFetchError`.
- **Compositional Data**: Assumes input taxa data is relative abundance (sums to 1). If not, CLR transformation is applied automatically.

## Verification
Run the integrity check to verify all artifacts:
```bash
python scripts/verify_integrity.py
```

## License
Research code for internal use. See `LICENSE` for details.
