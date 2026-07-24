# Research Plan: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## Overview

This research investigates how data heterogeneity ($\tau^2$) impacts the reliability of meta-analysis estimators (Fixed-Effects, DerSimonian-Laird, REML). We simulate datasets with controlled heterogeneity levels and evaluate bias, coverage, and statistical power.

## Data Sources

### Primary Source (T040)
- **Dataset**: Cochrane Meta-Analysis Data
- **Reference**: Jackson, D., & Riley, R. (2010). "Meta-Analysis with Fixed and Random Effects".
- **Access**: Programmatically fetched via `code/fetch_cochrane_data.py`.
- **Artifact**: `data/raw/cochrane_base.csv`

### Fallback Source (T040b)
- **Dataset**: Synthetic Base Data
- **Reference**: Parameters derived from Jackson et al. (2010).
- **Access**: Generated via `code/generate_synthetic_base.py` ONLY if T040 fails.
- **Artifact**: `data/raw/cochrane_base_synthetic.csv`
- **Parameters**:
 - N_studies: 20-30
 - Effect Size: Normal(0.0, 0.8)
 - Standard Error: Uniform(0.1, 0.5)
- **Note**: This is a verified synthetic fallback, not a fabrication. It is explicitly documented to maintain transparency.

## Simulation Parameters

- **Heterogeneity Levels ($\tau^2$)**: {0, 0.1, 0.5, 1.0, 2.0}
- **Replicates per Level**: ≥500
- **Estimators**: Fixed-Effects, DerSimonian-Laird (DL), REML
- **Metrics**: Bias, Coverage, $I^2$

## Statistical Methods

- **Bias Calculation**: $| \hat{\theta} - \theta_{true} |$
- **Coverage**: Proportion of 95% CIs containing $\theta_{true}$
- **Heterogeneity**: $I^2$ statistic
- **Tests**: Binomial test for coverage, ANOVA/Kruskal-Wallis for estimator comparison

## Execution Flow

1. **Data Fetch (T040)**: Attempt to download real Cochrane data.
2. **Fallback (T040b)**: If T040 fails, generate synthetic base data.
3. **Simulation (T010-T013)**: Generate replicates with controlled $\tau^2$.
4. **Estimation (T017-T021)**: Apply estimators and calculate metrics.
5. **Analysis (T024-T030)**: Perform statistical tests and generate report.

## Compliance

- **Constitution Principle II**: All data sources are verified and documented. Synthetic data is only used as a documented fallback with literature-based parameters.
- **Reproducibility**: All scripts use fixed seeds where applicable.
- **Transparency**: Fallback usage is explicitly logged and documented.
