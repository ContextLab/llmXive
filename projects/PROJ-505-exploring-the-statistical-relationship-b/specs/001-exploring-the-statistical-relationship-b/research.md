# Research: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Dataset Strategy

The project relies on time-series data from solar wind composition archives and geomagnetic indices. The following datasets are verified and used.

| Dataset | Variables Required | Source/URL (Verified) | Loader Method | Status/Notes |
|:--- |:--- |:--- |:--- |:--- |
| **ACE SWICS** | O/Fe, He/H, C/O ion fluxes; Velocity, Density, Temp | **NO VERIFIED SOURCE** (See "Verified datasets" block) | `pandas.read_csv` (from local raw files or synthetic) | **Critical Gap**: No verified source found. The plan will attempt to fetch from CDAWeb (expected to fail) and fallback to synthetic data generation. |
| **WIND Spacecraft** | Ion composition (if available), Bulk parameters | **NO VERIFIED SOURCE** (See "Verified datasets" block) | `pandas.read_csv` (from local raw files or synthetic) | **Critical Gap**: No verified source found. The OpenML "wind.csv" dataset is meteorological and **irrelevant**. The plan will fallback to synthetic data generation. |
| **NOAA Dst/Kp** | Dst index, Kp index | **NO VERIFIED SOURCE** (See "Verified datasets" block) | `pandas.read_csv` (from local raw files or synthetic) | **Critical Gap**: No verified source found. The listed NOAA buoy datasets are oceanographic and **irrelevant**. The plan will fallback to synthetic data generation. |
| **ij5/ace (HuggingFace)** | Bulk parameters (Velocity, Density, IMF) | ` | `zipfile` + `pandas.read_csv` | **Partial Use (Optional)**: May contain bulk parameters. If available, it will be used for bulk parameters; otherwise, synthetic data will be used for all variables. |

**Dataset Fit Analysis & Fatal Flaw Mitigation**:
The spec requires O/Fe, He/H, C/O from ACE SWICS/WIND and Dst/Kp from NOAA. The "Verified datasets" block **does not contain verified sources for any of these specific scientific datasets**. The listed URLs are for unrelated "wind" (weather) or "NOAA buoy" data.

**Decision**: The plan **cannot** proceed with the specific scientific analysis as defined in the spec because the required datasets (ACE SWICS composition, NOAA Dst/Kp) are **not available** in the verified list.
**Pivot**: The project will pivot to a **Methodology Demonstration & Pipeline Validation** using **synthetic data**.
**Revised Strategy**:
1. **Acknowledge the Gap**: The `research.md` and `plan.md` explicitly state that the required scientific datasets are missing from the verified sources.
2. **Synthetic Data Generation**: To demonstrate the *pipeline* (ingestion, alignment, regression, permutation testing) without the specific physics, the implementation will:
 * Use `generate_synthetic_data.py` to create a multi-year hourly dataset with realistic distributions for bulk parameters, composition ratios, and geomagnetic indices.
 * The synthetic data will be generated with known statistical properties (e.g., injected signals or null relationships) to validate the pipeline's ability to detect them.
3. **Pipeline Validation**: The statistical methods (regression, permutation, FDR) will be executed on the synthetic data to ensure the code works correctly.
4. **Explicit Limitations**: All outputs will clearly state that the results are for pipeline validation only and do not answer the scientific hypothesis about real solar wind composition.

*Note: If the user intended for the system to fetch from CDAWeb directly (which is not in the verified list), the system must flag this as a "Data Gap" and not proceed with real data ingestion.*

## Scientific Validity & Limitations

**Critical Limitation**: This project **does not** test the scientific hypothesis that "solar wind elemental composition independently predicts geomagnetic storm intensity." The required real-world data (ACE SWICS, NOAA Dst/Kp) is unavailable in the verified sources.
**Project Goal**: The project's goal is to **build and validate the statistical pipeline** for when real data becomes available. The synthetic data is used solely to ensure the code correctly implements:
* Temporal alignment of heterogeneous time series.
* Multivariate regression with coupling functions.
* Block permutation tests for time-series significance.
* FDR correction for multiple hypothesis testing.
* Cross-validation for out-of-sample performance.

**Implications**:
* The results (coefficients, p-values, R²) are **not** evidence for or against the scientific hypothesis.
* The success of the project is defined by the correct execution of the statistical methods and the generation of reproducible code artifacts.
* The project will explicitly document the data gap and the limitations of the findings.

## Statistical Methodology

### 1. Coupling Functions (Baseline)
To satisfy FR-004, the baseline model will use established coupling functions:
* **Akasofu Epsilon ($\epsilon$)**: $\epsilon = v B^2 \sin^4(\theta/2) l_0^2$, where $v$ is solar wind speed, $B$ is IMF magnitude, $\theta$ is clock angle, and $l_0$ is a scaling factor (~7 $R_E$).
* **Newell Function**: $d\Phi_{MP}/dt = v^{4/3} B_T^{2/3} \sin^{8/3}(\theta/2)$.

### 2. Multivariate Regression (FR-004, FR-005, FR-006)
* **Baseline Model**: $Y = \beta_0 + \beta_1 \epsilon + \beta_2 v + \beta_3 B + \epsilon_{resid}$
* **Full Model**: $Y = \beta_0 + \beta_1 \epsilon + \beta_2 v + \beta_3 B + \beta_4 (O/Fe) + \beta_5 (He/H) + \beta_6 (C/O) + \epsilon_{resid}$
* **Metric**: $\Delta R^2 = R^2_{full} - R^2_{baseline}$.

### 3. Cross-Validation (FR-007)
* **Method**: 5-Fold Time-Series Cross-Validation (using `TimeSeriesSplit` from `scikit-learn` to prevent look-ahead bias).
* **Metric**: Out-of-sample $R^2$.

### 4. Permutation Test (FR-008)
* **Method**: Block Permutation. Shuffling composition ratios in blocks of 24 hours to preserve temporal autocorrelation.
* **Iterations**: [deferred] (minimum).
* **Null Hypothesis**: Composition ratios have no predictive power beyond coupling functions.
* **Significance**: Observed coefficient $> 95^{th}$ percentile of null distribution.

### 5. Sensitivity & FDR (FR-009, FR-010)
* **Sensitivity**: Sweep $\alpha \in \{0.01, 0.05, 0.10\}$.
* **FDR**: Benjamini-Hochberg procedure applied to p-values of the three composition ratios across two indices (6 tests total).

### 6. Multicollinearity Check (FR-011)
* **Metric**: Variance Inflation Factor (VIF).
* **Threshold**: Flag if VIF $\ge 5$.

## Computational Feasibility

* **Data Size**: 20 years of hourly data $\approx [deferred]$ rows. This fits easily in GB RAM.
* **Compute**: Linear regression and permutation tests (with a sufficient number of iterations) on 175k rows are CPU-tractable. No GPU required.
* **Runtime**: Estimated < 1 hour on a standard CPU.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Verified Data** | **High**: Cannot answer the scientific question with real data. | **Mitigation**: Explicitly state the gap. Use synthetic data to validate the *pipeline* (code correctness) while clearly labeling results as synthetic. |
| **Temporal Autocorrelation** | **High**: Invalidates standard p-values. | **Mitigation**: Use Block Permutation (FR-008) and TimeSeriesSplit (FR-007). |
| **Multicollinearity** | **Medium**: Inflated standard errors. | **Mitigation**: Calculate VIF (FR-011) and report; if high, report descriptive statistics only. |
| **Synthetic Data Bias** | **Medium**: Synthetic data may not capture real-world complexities. | **Mitigation**: Document the limitations explicitly. Use synthetic data only for pipeline validation, not for scientific claims. |