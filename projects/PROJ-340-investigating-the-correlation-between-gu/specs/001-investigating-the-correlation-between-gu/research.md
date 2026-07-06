# Research: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Summary

This research phase validates the feasibility of the analysis pipeline by confirming dataset availability, variable fit, and statistical methodology constraints. The primary goal is to ensure that the required metagenomic and sleep architecture variables exist in a verified source before implementation begins.

**Critical Finding**: The "Verified datasets" block provided in the input **does not contain a single dataset** that satisfies the "Gut Microbiome + Sleep Architecture" requirement.
- The datasets listed (e.g., `snow_removal`, `invoices`, `butterflies`, `cat_kingdom`) are unrelated to the research topic.
- **Action Required**: The implementation MUST proceed with a **mock/synthetic dataset generator** for testing the pipeline logic, as no real-world public dataset matching the criteria is available in the verified list. The `research.md` must explicitly state this limitation.

**Scope Definition**: This project is currently scoped as a **Pipeline Validation Study**. The synthetic data is used to validate the *statistical engine* (correctness of ZINB, CLR, VIF, etc.) against known ground truths. It does **not** validate biological construct validity (actual gut-sleep correlations), which requires a real dataset.

## Dataset Strategy

The analysis requires a dataset containing **both** metagenomic sequencing counts (predictors) and polysomnography/actigraphy sleep metrics (outcomes) for the same subjects.

| Variable Category | Required Variables | Verified Source Status |
| :--- | :--- | :--- |
| **Metagenomic** | Taxon counts, Relative abundance | **NO VERIFIED SOURCE** found in the provided list. |
| **Sleep** | REM duration, SWS duration, Total Sleep Time | **NO VERIFIED SOURCE** found in the provided list. |

**Alternative Strategy (Synthetic Data)**:
Since no verified real dataset exists in the provided list, the pipeline will be tested using a synthetic dataset generator that:
1. Generates `N` rows of synthetic microbial counts (Zero-Inflated Negative Binomial distribution).
2. Generates `N` rows of synthetic sleep metrics (Normal or Beta distribution).
3. Injects a known, weak correlation structure (e.g., r=0.1) for validation purposes.
4. Allows the pipeline to run FR-001 through FR-007 successfully.
*Note: This validates the code's ability to recover known parameters, not biological truth.*

## Statistical Methodology

### 1. Compositional Data Handling (Mandatory)
Before any correlation analysis, microbial count data MUST be transformed to address the compositional nature (Aitchison geometry) which causes spurious correlations:
- **Method**: Centered Log-Ratio (CLR) transformation.
- **Implementation**: `scikit-bio` or custom implementation.
- **Rationale**: Converts relative abundance data into a Euclidean space suitable for standard correlation methods.

### 2. Correlation Method Selection (FR-002)
The pipeline will dynamically select the statistical test based on data distribution, strictly separating Zero-Inflation from Normality:
1. **Check Zero-Inflation**: Calculate proportion of zeros in microbial counts (after CLR or on raw counts depending on model).
   - If `zeros > 30%`: Use **Zero-Inflated Negative Binomial (ZINB)** or **Hurdle Model** (via `statsmodels`).
   - Else: Proceed to Normality check.
2. **Check Normality**: Perform Shapiro-Wilk test on the transformed (CLR) or non-zero-inflated data.
   - If `Shapiro-Wilk p < 0.05`: Use **Spearman Rank Correlation**.
   - Else: Use **Pearson Correlation**.

### 3. Multiple Comparison Correction (FR-003)
- Apply **Benjamini-Hochberg (BH)** procedure to all raw p-values.
- Target FDR: `q ≤ 0.05`.
- Output includes both raw and adjusted p-values.

### 4. Robustness & Diagnostics (FR-005, FR-006)
- **Sensitivity Analysis**: Re-calculate significance at `p < 0.01`, `p < 0.05`, `p < 0.10`. Report % change in significant findings.
- **Collinearity (VIF)**:
  - **Context**: Calculated in a **Multivariate Diagnostic Phase** (regressing one sleep metric against *all* taxa simultaneously), NOT in the pairwise correlation phase.
  - Check for perfect multicollinearity (matrix rank < number of predictors) for definitionally related taxa.
  - Calculate VIF for remaining predictors. Flag if `VIF > 5`.
- **Power Analysis**:
  - Calculate minimum `N` required to detect **r = 0.1** (realistic small effect) with `power ≥ 0.80` at `α = 0.05`.
  - Secondary check for `r = 0.3`.
  - Compare against actual `N`. Flag if underpowered for `r=0.1`.
- **Outlier Handling**:
  - Detect outliers in sleep metrics using the IQR method with a standard interquartile range multiplier.
  - Exclude outliers from correlation analysis.
  - Report the count of excluded points.

### 5. Framing (FR-004)
- All reports will explicitly state: "These results represent an **associational** relationship."
- Causal language (e.g., "causes", "leads to") is strictly prohibited.

## Compute Feasibility

- **Environment**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM, 6h limit).
- **Strategy**:
  - Synthetic data generation is computationally trivial.
  - ZINB models in `statsmodels` are CPU-tractable for `N < 1000`.
  - CLR transformation is lightweight.
  - No GPU required.
  - Memory footprint will be < 1GB for synthetic datasets.
- **Conclusion**: The pipeline is fully feasible within the constraints.

## Limitations

- **Data Availability**: No real-world dataset containing both gut microbiome and sleep architecture data was found in the verified list. The current plan relies on synthetic data for **pipeline logic validation only**. Future work requires sourcing a real dataset (e.g., from a specific biobank or published study) that meets the variable fit criteria to establish biological construct validity.
- **Observational Nature**: As per Assumption-001, the study is observational. Causal inference is not possible.
- **Construct Validity**: Synthetic data validates statistical engine correctness but cannot validate biological relationships.