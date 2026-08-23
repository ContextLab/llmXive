# Statistical Methods

This document describes the statistical methods used in the PROJ-340 pipeline.

## 1. Correlation Analysis

### 1.1. Pearson Correlation
- **Use Case**: Linear relationships between normally distributed variables.
- **Assumptions**: Normality, linearity, homoscedasticity.
- **Implementation**: `scipy.stats.pearsonr`

### 1.2. Spearman Correlation
- **Use Case**: Monotonic relationships, non-normal data.
- **Assumptions**: Ordinal data or rank-based.
- **Implementation**: `scipy.stats.spearmanr`

### 1.3. Zero-Inflated Negative Binomial (ZINB)
- **Use Case**: Count data with excess zeros (common in microbiome).
- **Assumptions**: Count data, zero-inflation.
- **Implementation**: `statsmodels.discrete.discrete_model.ZeroInflatedNegativeBinomialP`

## 2. Compositional Data Analysis

### 2.1. CLR Transformation
- **Use Case**: Handling compositional data (sum to 1).
- **Method**: Centered Log-Ratio transformation.
- **Implementation**: `code/transform.py`

### 2.2. SparCC / SpiecEasi
- **Use Case**: Correlation in compositional data.
- **Method**: Sparse Correlations for Compositional data.
- **Implementation**: Optional (requires external packages).

## 3. Multiple Testing Correction

### 3.1. Benjamini-Hochberg (FDR)
- **Use Case**: Controlling false discovery rate.
- **Method**: Rank-based p-value adjustment.
- **Implementation**: `code/analysis.py`

## 4. Diagnostics

### 4.1. Variance Inflation Factor (VIF)
- **Use Case**: Detecting multicollinearity.
- **Threshold**: VIF > 10 indicates high collinearity.
- **Implementation**: `code/diagnostics.py`

### 4.2. Power Analysis
- **Use Case**: Estimating required sample size.
- **Method**: Based on observed effect size and alpha.
- **Implementation**: `code/diagnostics.py`

### 4.3. Sensitivity Analysis
- **Use Case**: Assessing stability of results.
- **Method**: Re-running analysis at different p-value thresholds (0.01, 0.05, 0.10).
- **Implementation**: `code/diagnostics.py`

## 5. Outlier Detection

### 5.1. IQR Method
- **Use Case**: Identifying extreme values.
- **Method**: Values > 1.5x IQR above Q3 or < 1.5x IQR below Q1.
- **Implementation**: `code/ingest.py`

## 6. Causal Language Prevention

- **Method**: Regex scan for causal terms ("causes", "leads to", "effect").
- **Action**: Halt execution if found.
- **Implementation**: `code/report.py`

## 7. References

- Aitchison, J. (1982). The statistical analysis of compositional data.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate.
- Friedman, J., & Alm, E. J. (2012). Inferring correlation networks from genomic survey data.
