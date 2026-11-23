# Known Limitations

This document outlines the current limitations of the PROJ-340 pipeline.

## 1. Real Data Dependency

- **Strict Mode**: The pipeline is configured to fail if real data is not found. This is a deliberate design choice to prevent accidental use of synthetic data in research.
- **No Silent Fallback**: There is no automatic fallback to synthetic data if real data fetch fails. The user must explicitly switch to `--mode synthetic` for testing.

## 2. Compositional Data Handling

- **Package Dependencies**: Advanced compositional methods (SparCC, SpiecEasi) require external R packages or C++ compilers. If these are not installed, the pipeline falls back to standard correlation methods with a warning.
- **Normalization**: The pipeline assumes taxa abundances are either relative (sum to 1) or absolute counts. Mixed data types may lead to incorrect normalization.

## 3. Compute Resources

- **Timeout**: The pipeline enforces a 6-hour timeout. Large datasets (N > 10,000) with complex models (ZINB) may exceed this limit.
- **Memory**: The current implementation loads the entire dataset into memory. Datasets larger than available RAM will cause a crash. Streaming is not yet fully implemented for all stages.

## 4. Statistical Assumptions

- **Normality**: Pearson correlation assumes normality. The pipeline checks for this but may not detect all deviations.
- **Linearity**: Correlation methods assume linear relationships. Non-linear associations may be missed.
- **Causality**: The pipeline explicitly prevents causal language. It is a correlational study tool only.

## 5. Data Quality

- **Outliers**: The IQR method is robust but may not detect all types of outliers (e.g., multivariate outliers).
- **Missing Data**: Rows with missing values are excluded. Imputation is not currently supported.

## 6. Future Enhancements

- **Streaming**: Full support for streaming large datasets.
- **Imputation**: Methods for handling missing data.
- **Non-linear Methods**: Integration of mutual information or kernel-based methods.
- **GUI**: A web-based interface for non-technical users.
