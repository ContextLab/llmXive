# PROJ-131: The Impact of Perceived Social Support on Resilience to Online Harassment

## Overview

This project implements a statistical analysis pipeline to investigate the buffering effect of perceived social support on mental health outcomes (Depression, Anxiety, PTSD) following online harassment.

### Methodological Approach: Single-Dataset Analysis
**CRITICAL NOTE:** This analysis strictly follows the **Single-Dataset Approach** (Cyberbullying Survey 2021). The Spec's original requirement for a "Synthetic Cohort" (matching with GSS 2022) was identified as methodologically invalid in the project Plan and has been **excluded** from this implementation. All results are derived solely from the Cyberbullying Survey to ensure the interaction term estimates a genuine psychological buffering effect without confounding by dataset source.

## Prerequisites

### System Requirements
- Python 3.9+
- 2+ CPU cores
- 7GB+ RAM (for full dataset processing)
- ~14GB disk space for data artifacts

### Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```
*Note: The `requirements.txt` includes `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `ucimlrepo`, and other necessary libraries.*

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical modeling, bootstrapping, FDR correction
│ ├── data/ # Ingestion, preprocessing, cohort construction
│ ├── config/ # Configuration files (seeds, scales, bootstrap params)
│ └── main_pipeline.py # Main orchestration script
├── data/
│ ├── raw/ # Raw downloaded datasets (auto-generated)
│ └── results/ # Processed cohorts, regression outputs, reports
├── tests/ # Unit and contract tests
├── requirements.txt
└── README.md
```

## How to Run the Pipeline

### 1. Initialize Environment
Ensure the virtual environment is active and dependencies are installed.

### 2. Run the Full Pipeline
Execute the main orchestration script. This will:
1. Download and validate the Cyberbullying Survey 2021 dataset.
2. Perform MICE imputation and scale scoring.
3. Construct the analysis cohort.
4. Fit OLS models with interaction terms and HC3 standard errors.
5. Run 1,000 bootstrap resamples for confidence intervals.
6. Apply Benjamini-Hochberg FDR correction.
7. Perform sensitivity analyses (continuous severity, platform stratification).
8. Generate all reports and save results.

```bash
python code/main_pipeline.py
```

**Expected Runtime:** < 6 hours on a standard 2-core CPU (includes 1,000 bootstrap resamples).

### 3. Verify Execution
Check the logs and output files:
```bash
python code/quickstart_validator.py
```

## Expected Outputs

Upon successful completion, the following artifacts will be generated in `data/results/`:

| File | Description |
|:--- |:--- |
| `analysis_cohort.csv` | Cleaned, imputed analysis dataset |
| `validation_report.json` | Cohort validity checks (VIF, variance) |
| `regression_results.csv` | Model coefficients, SEs, p-values, bootstrap CIs |
| `regression_summary.md` | Human-readable interpretation of findings |
| `sensitivity_analysis.csv` | Results from alternative model specifications |
| `coefficient_comparison.csv` | Comparison of interaction term shifts |
| `data_lineage_report.md` | Trace of data transformations |
| `pipeline_run.log` | Detailed execution log |
| `reproducibility_audit.json` | SHA-256 hash verification of results |

## Data Sources

- **Primary Dataset:** Cyberbullying Survey 2021
 - **Source:** Loaded via `ucimlrepo` or direct CSV ingestion as configured in `code/data/ingestion.py`.
 - **Access:** The pipeline attempts to fetch this data automatically. If network access is restricted, ensure the raw file is placed in `data/raw/cyberbullying_2021.csv`.
- **Excluded:** GSS 2022 (per Methodological Pivot).

## Configuration

Key parameters are defined in `code/config/`:
- `seeds.yaml`: Random seeds for reproducibility.
- `scales.yaml`: Scoring weights for CES-D, GAD-7, PCL-5.
- `bootstrap_config.yaml`: Bootstrap resample count (1000), method (BCa), confidence level.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Run linting checks:
```bash
ruff check code/
```

## Limitations & Disclaimers

- **Associational Findings:** This analysis identifies statistical associations; it does not establish causal mechanisms.
- **Single Dataset:** Results are specific to the Cyberbullying Survey 2021 population and may not generalize to other contexts without further validation.
- **Missing Data:** The pipeline uses MICE imputation. If convergence fails (trace change > 0.01 over last 3 iterations), the pipeline halts with an error rather than proceeding with potentially biased estimates.