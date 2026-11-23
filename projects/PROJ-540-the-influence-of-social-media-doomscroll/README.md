# The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Project Overview

This project investigates the statistical relationship between social media "doomscrolling" (high-frequency news consumption) and anticipatory anxiety levels. We utilize real-world survey data to perform correlation analysis, multiple linear regression, and robustness checks to determine if increased news exposure predicts higher anxiety scores, controlling for baseline anxiety, age, and gender.

**Status**: ✅ Complete | **Data Source**: NHANES 2017-2018 (Verified) | **Pipeline**: Reproducible

## Quick Start

To run the full analysis pipeline:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the pipeline
python code/main.py
```

This will:
1. Download and stream the verified NHANES 2017-2018 dataset.
2. Validate schema and clean data (listwise deletion).
3. Perform construct validity checks (detect mathematical coupling).
4. Fit the OLS regression model and calculate correlations.
5. Run robustness checks on high-engagement subsets (if applicable).
6. Generate diagnostic plots, regression results, and a final report.

**Output Artifacts**:
- `data/processed/analysis_data.csv`: Cleaned dataset.
- `outputs/regression_results.json`: Model coefficients, p-values, VIF flags.
- `outputs/correlation_results.json`: Pearson/Spearman correlation matrices.
- `outputs/robustness_results.json`: Subset analysis results (or skip reason).
- `outputs/final_report.md`: Comprehensive analysis report.
- `outputs/plot.png`: Scatter plot with regression line.
- `outputs/diagnostics_residuals.png`, `outputs/diagnostics_qq.png`: Model diagnostics.

## Data Source & Verification

**Primary Source**: NHANES 2017-2018 Cycle (National Health and Nutrition Examination Survey)
**Variable Mapping**:
- `news_exposure_freq`: Mapped from media consumption variables (e.g., `DMQ010`).
- `anxiety_score`: Derived from anxiety assessment modules.
- `baseline_anxiety`: Pre-existing anxiety measures.
- `age`, `gender`: Demographic controls.

The pipeline includes a strict schema validator (`code/ingest.py`) that ensures the dataset contains the required columns. If the primary schema is not found, it attempts fallback sources (GSS, Pew, YouGov) in order. **No synthetic data is generated**; the pipeline fails loudly if real data cannot be retrieved.

## Methodology

### 1. Data Ingestion & Cleaning
- **Streaming**: Data is streamed in chunks to handle large datasets efficiently.
- **Validation**: Schema validation ensures required columns exist.
- **Cleaning**: Listwise deletion is applied for missing predictor/outcome values.
- **Power Check**: The pipeline halts with a `PowerLimitationError` if the final sample size (N) is less than 30, per Spec FR-002.

### 2. Statistical Modeling
- **Construct Validity**: Checks for mathematical coupling between `baseline_anxiety` and `anxiety_score`. If detected (same instrument/timepoint), `baseline_anxiety` is dropped, and a warning is logged.
- **Regression**: OLS model: `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`.
- **Assumptions**: Linearity, Homoscedasticity (Breusch-Pagan), Normality (Shapiro-Wilk).
- **Multicollinearity**: VIF flagging. If VIF > 10, the model is flagged as unstable, and the `news_exposure_freq` coefficient is set to `null`.

### 3. Robustness Check (Spec FR-006)
- If `social_media_engagement` is present and correlates with `news_exposure_freq` (r > 0.3), the top 25th percentile subset is analyzed.
- Coefficients and significance are compared between the full sample and the subset.
- If the condition is not met, the check is skipped and logged.

## Known Limitations

1. **Proxy Usage**: If `general_anxiety` is used as a proxy for `anticipatory_anxiety`, this is explicitly flagged in `outputs/regression_results.json` and the final report.
2. **VIF Instability**: High multicollinearity may render the `news_exposure_freq` coefficient unreliable; such cases are flagged and the coefficient is nullified.
3. **Data Availability**: The pipeline relies on public availability of the NHANES 2017-2018 dataset. If unavailable, it attempts fallbacks but will fail if none succeed.
4. **Sample Size**: Analyses with N < 30 are halted to prevent underpowered conclusions.

## Reproducibility

This project adheres to strict reproducibility principles:
- **Seeding**: A random seed is configured in `code/config.py` and logged to `data/processed/metadata.json`.
- **Determinism**: All stochastic operations (shuffling, sampling) use the seeded RNG.
- **Verification**: Re-running the pipeline with the same seed produces bitwise identical JSON outputs and statistically identical plots.
- **Audit**: The `audit_fabrication.py` script can be run to verify no synthetic data patterns exist in the outputs.

## Project Structure

```
projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── code/
│ ├── main.py # Pipeline orchestrator
│ ├── ingest.py # Data download, streaming, validation
│ ├── clean.py # Data cleaning, power checks
│ ├── model.py # Regression, correlations, diagnostics
│ ├── validity.py # Construct validity checks
│ ├── robustness.py # Robustness subset analysis
│ ├── viz.py # Plotting and report generation
│ ├── config.py # Environment and seed management
│ └──... # (Supporting modules)
├── data/
│ ├── raw/ # Downloaded raw data
│ └── processed/ # Cleaned data and metadata
├── outputs/
│ ├── regression_results.json
│ ├── correlation_results.json
│ ├── robustness_results.json
│ ├── final_report.md
│ └──... # Plots and logs
├── tests/
│ └──... # Unit and integration tests
├── requirements.txt
├── README.md
└── quickstart.md
```

## Success Criteria Verification

The pipeline automatically validates the following success criteria upon completion:
- **SC-001**: P-value for `news_exposure_freq` is present and compared to 0.05.
- **SC-002**: R-squared is present and reported.
- **SC-003**: Robustness check results (or skip reason) are documented.
- **SC-004**: Assumption check results (Shapiro-Wilk) are reported.
- **SC-005**: Benchmark runtime is < 60 seconds.

Results of this validation are saved to `outputs/success_criteria_validation.json`.

## License & Citation

This analysis is for research purposes. Data is sourced from public government surveys (NHANES).
Please cite the source dataset appropriately in any publications.