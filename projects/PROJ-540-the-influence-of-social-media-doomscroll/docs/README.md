# Project Documentation: PROJ-540

## Technical Specifications

### Data Model
The core dataset must contain the following columns:
- `news_exposure_freq`: Frequency of news consumption (predictor).
- `anxiety_score`: Outcome variable (anticipatory/general anxiety).
- `baseline_anxiety`: Pre-existing anxiety measure (covariate).
- `age`: Participant age.
- `gender`: Participant gender.

### Statistical Methods
1. **Correlation**: Pearson or Spearman correlation calculated between `news_exposure_freq` and `anxiety_score`.
2. **Regression**: Multiple Linear Regression (OLS) using the formula:
 `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`
3. **Diagnostics**:
 - Linearity check.
 - Homoscedasticity (Breusch-Pagan test).
 - Normality of residuals (Shapiro-Wilk test).
 - Multicollinearity (Variance Inflation Factor, VIF).
4. **Robustness**: Re-fitting the model on the top 25th percentile of `social_media_engagement` if correlated with exposure.

### Error Handling
- **PowerLimitationError**: Raised if cleaned N < 130.
- **MathematicalCouplingError**: Raised if `baseline_anxiety` and `anxiety_score` are not distinct constructs or if VIF > 10.
- **DataValidationError**: Raised if schema validation fails.

### Reproducibility
- All random seeds are set via `config.py` and logged.
- The pipeline fails loudly if the real dataset URL is unreachable (no synthetic fallback).

## API Reference

### `code/ingest.py`
- `download_data(url, output_path)`: Fetches data.
- `validate_schema(df)`: Checks required columns.
- `clean_data(df)`: Handles missing values and power checks.

### `code/model.py`
- `fit_regression_model(df)`: Returns OLS results.
- `calculate_correlation(df)`: Returns correlation metrics.
- `check_assumptions(df)`: Runs diagnostic tests.

### `code/validity.py`
- `check_construct_validity(df)`: Ensures distinct constructs.

### `code/viz.py`
- `plot_scatter_with_regression(df)`: Generates diagnostic plots.

## Development Guidelines
- Use `pytest` for testing.
- Adhere to Black formatting (line-length 88).
- Log all critical steps to `outputs/analysis.log`.
