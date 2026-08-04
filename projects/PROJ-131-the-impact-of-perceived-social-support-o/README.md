# The Impact of Perceived Social Support on Resilience to Online Harassment

**Project ID**: PROJ-131
**Status**: Production Ready
**Methodology**: Single-Dataset Analysis (Cyberbullying Survey 2021)

## Overview

This project implements a rigorous statistical analysis to determine if perceived social support buffers the negative psychological effects of online harassment. The pipeline ingests the **Cyberbullying Survey 2021**, harmonizes variables, applies Multiple Imputation by Chained Equations (MICE), and fits robust OLS models with interaction terms.

**Critical Methodological Note**: This implementation strictly follows the **Revised Approach** (Single-Dataset Analysis). The original Spec's requirement for a "Synthetic Cohort" matching GSS 2022 data was deemed methodologically invalid and has been excluded. All analyses are performed on the single, verified Cyberbullying Survey dataset to ensure the interaction term estimates a genuine psychological buffering effect without confounding by dataset source.

## Prerequisites

- **Python**: 3.9+
- **System Dependencies**: `pip`, `python3-venv`
- **Data Source**: The pipeline automatically downloads the **Cyberbullying Survey 2021** from the UCI Machine Learning Repository (or the verified Hugging Face dataset ID) at runtime. No manual download is required, but a stable internet connection is necessary.

## Installation

1. **Clone the repository** and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-131-the-impact-of-perceived-social-support-o
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

## Methodological Approach

### Single-Dataset Analysis
The pipeline exclusively uses the **Cyberbullying Survey 2021**.
- **Excluded**: GSS 2022 (Excluded per Plan's 'Revised Approach' due to methodological invalidity of synthetic matching).
- **Source**: Real, programmatically accessible data fetched at runtime.
- **Imputation**: MICE (m=5, max_iter=10) for predictors.
- **Modeling**: OLS with HC3 standard errors and Bias-Corrected Accelerated (BCa) Bootstrap CIs (1,000 resamples).
- **Correction**: Benjamini-Hochberg FDR for multiple outcomes (Depression, Anxiety, PTSD).

## Running the Pipeline

Execute the full end-to-end analysis:

```bash
python code/main_pipeline.py
```

**What this does**:
1. **Ingestion**: Downloads and validates the Cyberbullying Survey 2021.
2. **Preprocessing**: Applies MICE imputation and scales scoring.
3. **Cohort Construction**: Filters for validity and variance.
4. **Modeling**: Fits interaction models and computes bootstrap CIs.
5. **Sensitivity Analysis**: Tests robustness with continuous severity and platform stratification.
6. **Reporting**: Generates markdown summaries and CSV results.

**Expected Runtime**: < 6 hours on a standard 2-core CPU (verified).

## Expected Outputs

Upon successful completion, the following artifacts will be generated in `data/results/`:

| File | Description |
|------|-------------|
| `analysis_cohort.csv` | The cleaned, validated analysis dataset. |
| `regression_results.csv` | Model coefficients, SEs, p-values, and bootstrap CIs. |
| `regression_summary.md` | Human-readable interpretation of the interaction effects. |
| `sensitivity_analysis.csv` | Results from alternative model specifications. |
| `coefficient_comparison.csv` | Comparison of baseline vs. sensitivity coefficients. |
| `data_lineage_report.md` | Audit trail of data transformations. |
| `reproducibility_audit.json` | Hash verification of results. |
| `pipeline_run.log` | Detailed execution log. |

## Project Structure

```
code/
├── data/
│ ├── ingestion.py # Data fetching and validation
│ ├── preprocessing.py # MICE imputation and scaling
│ └── cohort.py # Cohort construction
├── analysis/
│ ├── models.py # OLS fitting and bootstrapping
│ ├── sensitivity.py # Robustness checks
│ ├── fdr_correction.py # Multiple comparison correction
│ └── results.py # Report generation
├── main_pipeline.py # Orchestration entry point
└── requirements.txt # Dependencies

data/
├── raw/ # Raw downloaded data
└── results/ # Final analysis artifacts
```

## Reproducibility & Safety

- **Seeding**: All random operations use `random_seed: 42` from `config/seeds.yaml`.
- **Fail Loudly**: If the real data source cannot be fetched, the pipeline raises a `RuntimeError` and **never** falls back to synthetic data.
- **Validation**: A reproducibility audit compares run hashes to ensure deterministic results.

## License

This project is part of the llmXive automated science pipeline.

## Contact

For issues related to data fetching or execution failures, refer to `data/results/pipeline_run.log`.