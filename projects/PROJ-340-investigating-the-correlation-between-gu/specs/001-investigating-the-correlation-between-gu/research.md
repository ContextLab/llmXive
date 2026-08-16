# Research: Gut Microbiome-Sleep Architecture Correlation

## Summary

This research phase establishes the statistical methodology, data strategy, and feasibility of investigating the correlation between gut microbiome composition and sleep architecture. The primary challenge is the **absence of a verified, open-source dataset** containing both metagenomic sequencing data and concurrent polysomnography/actigraphy metrics for the same subjects. Consequently, the plan relies on a **deterministic synthetic data generation strategy** (Dirichlet-Multinomial) for pipeline validation and robustness testing, while explicitly documenting the data gap for real-world deployment.

## Dataset Strategy

### The Data Gap
A search for public datasets containing both **gut microbiome composition** (taxonomic counts) and **sleep architecture** (REM, SWS, NREM durations/percentages) yielded no verified, directly downloadable sources.
- **Gut Microbiome**: Abundant in HuggingFace (e.g., Qiita, MG-RAST exports), but rarely paired with sleep data.
- **Sleep Architecture**: Available in MESA, SHHS, or PhysioNet, but rarely paired with microbiome data.
- **Joint Datasets**: No open dataset matches the spec requirement (FR-001) for a single cohort with both modalities.

**Conclusion**: The project **cannot** proceed with real data in its current scope. The implementation will use a **deterministic synthetic data generator** (`code/synthetic_data.py`) that mimics the statistical properties (zero-inflation, over-dispersion, compositional sum constraint) described in the spec. This allows the pipeline to be tested for robustness, error handling, and statistical correctness (FR-002, FR-003) without violating the "Verified Accuracy" or "Data Hygiene" principles.

**Fallback Strategy**: If a joint dataset becomes available (e.g., a new PhysioNet study), the pipeline can switch to `--mode real` by removing `validation_mode_flag.json`. The search criteria for such a dataset are: "metagenomic sequencing" AND ("polysomnography" OR "actigraphy") AND "human cohort".

### Verified Datasets (for reference only)
*The following datasets were verified for format/availability but DO NOT contain the required joint variables. They are cited here to demonstrate the search effort and to define what a "real" substitute would look like.*

| Dataset Name | Type | Variables Present | Missing Variables | Status |
|:--- |:--- |:--- |:---:--- |
| **MESA Sleep** | PhysioNet (Access Gated) | Sleep metrics | Microbiome counts | **Unsuitable** (Access Gated) |
| **SHHS** | PhysioNet (Access Gated) | Sleep metrics | Microbiome counts | **Unsuitable** (Access Gated) |
| **Qiita Microbiome** | HuggingFace (Open) | Microbiome counts | Sleep metrics | **Unsuitable** (Missing Outcome) |
| **HuggingFace: Sleep** | HuggingFace (Open) | Sleep metrics | Microbiome counts | **Unsuitable** (Missing Predictor) |

*Note: As per the "Verified Accuracy" principle, no URLs for "Gut Microbiome + Sleep" datasets are cited because none exist in the verified block. The plan proceeds with synthetic data.*

## Statistical Methodology

### 1. Preprocessing: Compositional Data Analysis (CoDA)
Microbiome data is **compositional** (sums to a constant total). Standard correlations on raw counts are invalid due to the closure problem.
- **Action**: Apply **Centered Log-Ratio (CLR)** transformation to all predictor variables (taxa) before any statistical test.
- **Formula**: $clr(x_i) = \ln(x_i / g(x))$, where $g(x)$ is the geometric mean of the composition.
- **Outcome**: This transforms data to Euclidean space, making Pearson/Spearman correlations valid and removing spurious collinearity.

### 2. Method Selection Logic (FR-002)
The system will dynamically select the correlation method based on the **CLR-transformed** data distribution:
1. **Zero-Inflated Negative Binomial (ZINB) / Hurdle Model**: Selected if:
 * Proportion of zeros in raw counts > 30% **OR**
 * Over-dispersion ratio (variance/mean) > 1.5.
 * *Rationale*: Handles excess zeros and over-dispersion. Coefficients are reported as log-rate ratios.
2. **Spearman Rank Correlation**: Selected if:
 * Proportion of zeros ≤ 30% **AND**
 * Shapiro-Wilk test p-value < 0.05 (non-normal).
 * *Rationale*: Robust to non-normality in CLR space.
3. **Pearson Correlation**: Selected if:
 * Proportion of zeros ≤ 30% **AND**
 * Shapiro-Wilk test p-value ≥ 0.05 (normal).
 * *Rationale*: Maximum power for normally distributed CLR data.

### 3. Multiple Comparison Correction (FR-003)
- **Method**: Benjamini-Hochberg (BH) procedure.
- **Target**: Control False Discovery Rate (FDR) at q ≤ 0.05.
- **Implementation**: All raw p-values from the correlation matrix will be adjusted. Results will be flagged as `is_significant` only if `p_adjusted < 0.05`.

### 4. Collinearity Diagnostics (FR-006)
- **Perfect Multicollinearity**: Detected via **Matrix Rank Check** on the CLR-transformed predictor matrix. If rank < number of predictors, the system flags "Perfect Multicollinearity" and excludes the dependent pair from VIF calculation.
- **Variance Inflation Factor (VIF)**: Calculated for all remaining predictors on the **CLR-transformed** data.
 - Threshold: VIF > 5 triggers a warning.
 - *Note*: The value "33" (flag vif = 33) from the verified facts (Q113106917) is noted but not used as a hard threshold; the standard 5.0 is used for flagging.
- **Definitional Pairs**: Taxa in the same hierarchy (e.g., Genus A and Family containing Genus A) are checked for linear dependence.

### 5. Sensitivity Analysis (FR-005)
- **Thresholds**: p < 0.01, p < 0.05, p < 0.10.
- **Metric**: Percentage change in the number of significant findings compared to the baseline (p < 0.05).
- **Stability Score**: Coefficient of variation of significant counts across thresholds.

### 6. Power Analysis (US-3)
- **Target**: Detect correlation r ≥ 0.3 with Power ≥ 0.80 at α = 0.05.
- **Method**:
 - For **Correlation**: `pwr.r.test` with an inflation factor for the number of tests (FDR).
 - For **ZINB**: Simulation-based power analysis (generate data with known parameters, fit model, estimate power).
- **Action**: If N < calculated minimum, flag "Power Limitation" in the report.

### 7. Synthetic Data Generation
- **Model**: **Dirichlet-Multinomial** distribution.
- **Properties**: Explicitly models zero-inflation, over-dispersion, and the compositional sum constraint.
- **Validation**: The generator includes a `ground_truths` mapping to verify that the pipeline correctly detects the injected correlations.

## Compute Feasibility

- **CPU-First**: All methods (ZINB, Spearman, VIF, Power Analysis) are computationally tractable on a 2-core CPU runner for N < 1000.
- **Memory**: Estimated < 1 GB RAM for N=1000, 500 taxa.
- **Time**: Expected runtime < 30 minutes for synthetic data; < 2 hours for real data (if available).
- **GPU**: Not required. ZINB models in `statsmodels` are CPU-optimized.

## Ethical & Interpretative Constraints

- **Associational Framing**: All reports will explicitly state: "These results represent an associational relationship. No causal claims are made." (FR-004).
- **Observational Nature**: The plan assumes no randomization; therefore, confounding variables (diet, age, medication) are acknowledged as potential limitations if real data were used.

## References

- **Benjamini-Hochberg**: Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate. DOI: []
- **ZINB Models**: Lambert, D. (1992). Zero-Inflated Poisson Regression. DOI: []
- **VIF**: Fox, J., & Monette, G. (1992). Generalized Collinearity Diagnostics. DOI: [10.1080/01621459.1992.10475190](https://doi.org/10.1080/01621459.1992.10475190)
- **Compositional Data**: Aitchison, J. (1986). The Statistical Analysis of Compositional Data. DOI: []
- **Dataset Search**: Verified against PhysioNet, HuggingFace, and UCI repositories. No joint dataset found.