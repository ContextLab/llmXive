# PROJ-018: Adoption of Sustainable Agricultural Practices in Low-Income Areas

## Overview

This project investigates the relationship between community engagement and the adoption of sustainable agricultural practices in low-income regions. Using survey data, we construct a community engagement score and analyze its impact on sustainable practice adoption while controlling for covariates such as farm size, education, and access to credit.

## Project Structure

```
code/
 ├── 00_generate_synthetic_data.py # Synthetic data generator
 ├── 01_download_data.py # Data acquisition (real or synthetic)
 ├── 02_clean_data.py # Data cleaning and validation
 ├── 03_engineer_features.py # Feature engineering (scores, indicators)
 ├── 04_model_analysis.py # Statistical modeling and mediation
 ├── 05_generate_report.py # PDF report generation
 ├── 06_finalize_results.py # Finalization and logging
 ├── config.py # Configuration management
 └── logging_config.py # Logging infrastructure
data/
 ├── raw/ # Raw downloaded data
 └── processed/ # Cleaned and engineered data
results/
 ├── validity_metrics.yaml # Reliability and validity checks
 └── model_results.yaml # Regression and mediation results
docs/
 ├── README.md # This file
 └── METHODOLOGY.md # Detailed methodology notes
specs/
 └── 018-adoption-sustainable-agriculture/
 └── contracts/ # Data and results schema contracts
```

## Data Provenance

### Primary Data Sources

1. **World Bank LSMS (Living Standards Measurement Study)**
 - Target: Agricultural module surveys from low-income countries
 - Variables: Farm characteristics, adoption of practices, household demographics
 - Access: Programmatic fetch via World Bank API (fallback to synthetic if unavailable)

2. **FAO FIES (Food Insecurity Experience Scale)**
 - Target: Community engagement and food security indicators
 - Variables: Membership in cooperatives, extension service participation
 - Access: Programmatic fetch via FAO API (fallback to synthetic if unavailable)

### Data Processing Pipeline

The pipeline follows a strict sequential flow:

1. **Acquisition (T012)**: Attempts to fetch real data from World Bank/FAO APIs. If endpoints are unreachable or rate-limited, the system falls back to the synthetic data generator (`00_generate_synthetic_data.py`) which produces statistically consistent mock data. The source (real vs. synthetic) is logged in `data/metadata.yaml`.

2. **Cleaning (T014)**: Raw data is processed by `02_clean_data.py` to handle missing values (imputation or dropping rows with >30% missing), normalize categorical codes, and validate required fields. Output: `data/processed/cleaned_data.csv`.

3. **Feature Engineering (T022)**: `03_engineer_features.py` constructs:
 - `adoption_binary`: 1 if any sustainable practice reported
 - `engagement_score`: Composite index from proxy variables (membership, extension, collective action)
 - Reliability metrics (Cronbach's α) and validity checks (EFA with Principal Axis Factoring)
 Output: `data/processed/engineered_data.csv` and `results/validity_metrics.yaml`.

4. **Modeling (T040)**: `04_model_analysis.py` performs logistic regression, VIF diagnostics, FDR correction, ROC analysis, and mediation analysis with sensitivity checks (E-values, Rosenbaum bounds). Output: `results/model_results.yaml`.

5. **Reporting (T042)**: `05_generate_report.py` compiles all results into a reproducible PDF report.

### Limitations

- **Real Data Access**: If World Bank or FAO APIs are unavailable, the pipeline relies on synthetic data. This is documented as a limitation in `data/metadata.yaml` (FR-001, FR-002).
- **Power Analysis**: If the effective sample size for events is insufficient (ratio < 10), a warning is logged but execution continues (SC-006).
- **Mediation Analysis**: Results are labeled as "exploratory" due to the observational nature of the data (FR-012).

## Execution

To run the full pipeline:

```bash
# Ensure dependencies are installed
pip install -r code/requirements.txt

# Run data acquisition and cleaning
python code/01_download_data.py
python code/02_clean_data.py

# Run feature engineering
python code/03_engineer_features.py

# Run statistical analysis
python code/04_model_analysis.py

# Generate report
python code/05_generate_report.py
```

## Outputs

- `data/processed/cleaned_data.csv`: Cleaned survey data
- `data/processed/engineered_data.csv`: Data with engagement score and adoption indicator
- `results/validity_metrics.yaml`: Reliability and validity statistics
- `results/model_results.yaml`: Regression coefficients, VIF, AUC, mediation results
- `results/report.pdf`: Comprehensive PDF report

## License

This project is for research purposes. Data usage complies with source terms (World Bank, FAO).
