# Research: Pipeline Validation Study: Gut Microbiome & Cognitive Flexibility Analysis

## Dataset Strategy

The analysis requires two primary data modalities: 16S rRNA sequencing data (or pre-calculated diversity metrics) and cognitive flexibility scores, linked by a unique participant ID. The target demographic is adults aged 65+.

### Verified Datasets

Per the project constraints, we must cite only verified sources. The "# Verified datasets" block provided for this project **does not contain a verified source for 16S rRNA sequencing data linked to cognitive flexibility in aging**.

- **Microbiome Data**: NO verified source found.
- **Cognitive Data**: NO verified source found.
- **BMI/Covariate Data**: While BMI datasets exist in the verified block, they are not linked to microbiome data or cognitive scores.

**Decision**: Since no verified dataset exists in the provided list that satisfies the spec's requirement (linked microbiome + cognitive data for age 65+), the implementation plan proceeds with a **Synthetic Dataset Generator** for the purpose of **Pipeline Validation**.

**Scope Amendment**: The project scope is amended from "Investigating Correlation" to **"Pipeline Validation Study"**. The synthetic data will be generated under a **Null Hypothesis** (zero correlation between microbiome diversity and cognitive flexibility) to validate that the pipeline correctly returns non-significant results (p > 0.05) when no effect exists. This avoids the tautology of generating data with a pre-defined correlation and then "detecting" it.

### Data Processing Strategy

1.  **Synthetic Generation (Null Hypothesis)**: A script will generate a synthetic dataset mimicking the expected structure of the UK Biobank microbiome-cognitive link, but with **independent** variables.
    -   `participant_id`: Unique integer.
    -   `age`: Uniform distribution 65-85.
    -   `sex`: Binary (0/1).
    -   `bmi`: Normal distribution.
    -   `dietary_fiber`: Normal distribution.
    -   `antibiotic_use`: Binary (0/1).
    -   `microbiome_sample_id`: Linked to participant.
    -   `shannon_diversity`: Normal distribution (mean ~3.5, std ~0.5).
    -   `simpson_diversity`: Normal distribution.
    -   `chao1`: Normal distribution.
    -   `bray_curtis_distance`: Matrix (pre-calculated or simulated).
    -   `cognitive_flexibility_score`: Normal distribution, **statistically independent** of `shannon_diversity` (correlation ~ 0).

2.  **Filtering**: Apply `age >= 65` and non-null checks for all required variables (FR-002).

3.  **Normalization**: Log-transform diversity metrics if skewed.

## Statistical Methodology

### Alpha Diversity Correlation (FR-004)

-   **Test**: Pearson correlation if normality holds (Shapiro-Wilk p > 0.05); otherwise Spearman rank correlation.
-   **Output**: Correlation coefficient ($r$), p-value, 95% CI.
-   **Correction**: Benjamini-Hochberg (BH) for multiple comparisons across Shannon, Simpson, and Chao1.
-   **Validation Goal**: Verify that $p > 0.05$ (failure to reject null) for the independent synthetic data.

### Linear Regression (FR-005)

-   **Model**: $CognitiveFlexibility = \beta_0 + \beta_1(Diversity) + \beta_2(Age) + \beta_3(Sex) + \beta_4(BMI) + \beta_5(Fiber) + \beta_6(Antibiotics) + \epsilon$
-   **Method**: Ordinary Least Squares (OLS) via `statsmodels`.
-   **Covariates**: Age, Sex, BMI, Dietary Fiber, Antibiotic Use.
-   **Diagnostics**: VIF for collinearity (acknowledging potential collinearity between fiber and BMI).
-   **Correction**: BH correction for multiple diversity metrics tested.
-   **Validation Goal**: Verify that $\beta_1$ is not significantly different from zero.

### Beta Diversity (PERMANOVA/db-RDA) (FR-005)

-   **Method**: Permutational Multivariate Analysis of Variance (PERMANOVA) or Distance-based Redundancy Analysis (db-RDA) using `skbio.stats.distance.permanova` or `vegan` (via `rpy2` if needed, else pure Python equivalent).
-   **Input**: Bray-Curtis or UniFrac distance matrix.
-   **Factor**: **Continuous** Cognitive Flexibility Score (avoiding arbitrary quartile binning which loses power).
-   **Output**: $R^2$, p-value.
-   **Validation Goal**: Verify that the model explains no significant variance in the beta diversity matrix.

### Power Analysis (FR-007)

-   **Method**: **A priori** Power Analysis.
-   **Basis**: Effect sizes derived from **general literature** on microbiome-cognition relationships (e.g., typical $r$ values reported in aging studies, e.g., $r \approx 0.1-0.2$). *Note: These are assumptions for simulation design, not verified findings for the specific UK Biobank context.*
-   **Goal**: Determine the sample size required to detect a "typical" effect size with 80% power at $\alpha=0.05$. This justifies the size of the synthetic dataset used for validation.

## Sensitivity & Confounding Analysis

To address the concern about unmeasured confounders:
-   **E-value Calculation**: Calculate E-values for the observed correlation (expected to be near zero) to quantify the minimum strength of association an unmeasured confounder would need to explain away the result.
-   **Negative Control**: In a secondary validation run, artificially inject a known confounder (e.g., a variable correlated with both diet and microbiome) to verify the regression model detects the spurious correlation, confirming the pipeline's sensitivity to confounding.

## Edge Case Handling

-   **Zero Variance**: If `shannon_diversity` has zero variance (all samples identical), the system logs a warning and skips correlation calculation to avoid division by zero.
-   **Missing Covariates**: Listwise deletion (exclude participant) or mean imputation (logged). Default: Listwise deletion for regression.
-   **Non-Normality**: Auto-switch to Spearman if skewness > 1.0 or Shapiro-Wilk p < 0.05.

## Decision Rationale

-   **Synthetic Data (Null Hypothesis)**: Chosen because no verified dataset URL exists. The data is generated with **zero correlation** to validate the pipeline's ability to correctly identify *no effect*, avoiding circular validation.
-   **CPU-Only**: All selected libraries (`scipy`, `statsmodels`, `scikit-learn`) have efficient CPU implementations. No GPU acceleration is required for correlation/regression on <1000 samples.
-   **BH Correction**: Essential for FR-005 to control FDR across multiple diversity metrics.
-   **A priori Power**: Replaces post-hoc power to ensure valid sample size justification for the simulation.
-   **Continuous Covariate**: Replaces quartile binning to maintain statistical power and align with standard microbiome practices.