# Research Methodology: Statistical Analysis of CMIP6 Ensembles

## Overview

This document outlines the methodological justification for the statistical techniques employed in the analysis of publicly available CMIP6 climate model output ensembles. The pipeline prioritizes robustness, reproducibility, and the preservation of derivative structures inherent in climate time-series data.

## 1. Functional Data Representation via B-Splines

### 1.1 Rationale
Climate model outputs are inherently continuous processes observed at discrete time steps. Traditional discrete statistical methods (e.g., standard PCA on time-points) fail to capture the smoothness and derivative properties (e.g., rates of change, acceleration) of climate variables.

### 1.2 Spline-Based Imputation
Missing values in CMIP6 ensembles are handled via **spline-based imputation** rather than simple linear interpolation or mean imputation.
- **Justification**: Spline interpolation preserves the local smoothness and curvature of the underlying climate signal.
- **Method**: We utilize `scipy.interpolate.UnivariateSpline` with Generalized Cross-Validation (GCV) to select the smoothing parameter. This ensures that the imputed values are consistent with the observed derivatives of the time series, preventing artificial discontinuities that could distort subsequent functional analysis.
- **Fallback**: Linear interpolation is used only if the spline fit fails to converge, ensuring pipeline robustness without compromising the primary methodology.

### 1.3 Basis Dimension Selection
The global basis dimension $K$ is determined via pilot GCV/AIC selection (Task T015). This data-driven approach balances model complexity against overfitting, ensuring that the functional representation captures the essential variance without noise amplification.

## 2. Functional Principal Component Analysis (fPCA)

### 2.1 Dominant Mode Extraction
fPCA is employed to identify the dominant spatiotemporal modes of variability within the ensemble.
- **Advantage over Standard PCA**: By operating on the functional coefficients (B-spline basis) rather than raw time points, fPCA yields smooth eigenfunctions that are directly interpretable as physical modes of variation (e.g., seasonal cycles, long-term trends).
- **Implementation**: We use the `scikit-fda` library to perform the decomposition, calculating eigenvalues and eigenfunctions that maximize the explained functional variance.

### 2.2 Variance Stopping Criterion
The analysis stops early if the cumulative variance of the extracted components reaches 80% (Task T023). This threshold ensures that the reduced-dimensional representation retains the vast majority of the ensemble's signal while significantly reducing computational complexity for downstream robustness checks.

## 3. Robustness Assessment: Leave-One-Out (LOO) Jackknife

### 3.1 Methodological Justification
The stability of the identified dominant modes is assessed using a **Leave-One-Out (LOO) Jackknife** protocol (Task T028). This is a rigorous resampling technique mandated by FR-004 and Constitution Principle VI to ensure that results are not driven by a single outlier model or a specific family of models.

### 3.2 Protocol Details
- **Iteration Count**: The procedure runs exactly $N$ iterations, where $N$ is the total number of ensemble members (Task T028a). In each iteration $i$, the $i$-th model is removed from the dataset, and the fPCA is re-executed on the remaining $N-1$ models.
- **Alignment**: Before comparison, eigenfunctions from each LOO subsample are aligned to the full-ensemble eigenfunctions using **Procrustes analysis** (Task T029). This step corrects for sign ambiguities (eigenfunctions can flip signs arbitrarily) and rotational differences, ensuring a fair comparison of the mode shapes.
- **Stability Metric**: We calculate the correlation between the loadings (scores) of the full ensemble and each LOO subsample.
 - **Threshold**: Modes with a correlation coefficient $< 0.95$ are flagged as unstable (Task T030).
 - **Output**: Specific ensemble members causing instability are identified and logged to `artifacts/unstable_modes.json`.

### 3.3 Effectiveness
The LOO Jackknife is superior to bootstrapping for this application because:
1. **Deterministic Coverage**: It systematically tests the influence of *every* single model, providing a complete map of sensitivity.
2. **Small Sample Correction**: Climate ensembles often have a limited number of models ($N \approx 30-50$). LOO is the most efficient way to estimate the variance of the estimator in small-sample regimes without introducing the additional variance of random resampling.
3. **Model Family Detection**: By removing one model at a time, we can detect if a specific model (or a cluster of similar models) is disproportionately driving a dominant mode, which is critical for understanding model bias in CMIP6.

## 4. Data Integrity and Reproducibility

- **Real Data Source**: All analysis is performed on real CMIP6 data downloaded from the `sungduk/wip_cmip6` Hugging Face dataset repository. No synthetic or placeholder data is used.
- **State Management**: Artifact hashes are computed and updated after every major processing step (Task T006) to ensure the reproducibility of the entire pipeline.
- **Logging**: JSON-formatted logs at INFO, DEBUG, and ERROR levels provide a complete audit trail of the analysis (Task T007).

## References
- Ramsay, J. O., & Silverman, B. W. (2005). *Functional Data Analysis*. Springer.
- CMIP6 Data Documentation. Earth System Grid Federation.
- `scikit-fda` Documentation: Functional Data Analysis in Python.