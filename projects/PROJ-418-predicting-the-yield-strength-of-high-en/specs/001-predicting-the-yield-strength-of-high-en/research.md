# Research: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Dataset Strategy

### Primary Dataset: HEA Compositions & Yield Strength
*   **Source**: Zenodo Dataset (DOI: `10.5281/zenodo.3935596`).
*   **Content**: Elemental fractions, phase structure, testing temperature, yield strength (MPa).
*   **Verified Source Constraint**: This is the **only** permitted source. If this DOI is unreachable, the pipeline fails with "Verified Source Unreachable". No fallbacks to NIST or Materials Project are allowed (Spec FR-001 must be updated to reflect this).

### Elemental Properties
*   **Source**: Bundled static CSV (`data/raw/elemental_properties.csv`), version 1.0, derived from CRC Handbook 97th Ed.
*   **Content**: Atomic radii, electronegativity, valence electron counts.
*   **Reproducibility**: Using a static, versioned file ensures deterministic descriptor engineering (Constitution VI). The file will be checksummed upon ingestion.

### Data Availability & Feasibility
*   **Streaming**: If the dataset exceeds a substantial size threshold, the pipeline will stream it.
*   **Sample Size**: If the filtered count of single-phase room-temperature alloys is <500, the pipeline flags a "Data Limitation" warning.
*   **Unit Normalization**: All yield strength values converted to MPa.

## Methodology & Statistical Rigor

### 1. Descriptor Engineering (FR-002, FR-003)
*   **Formulas**:
    *   **Atomic Size Mismatch (δ)**: $\delta = \sqrt{\sum c_i (1 - r_i/\bar{r})^2} \times 100$
    *   **Electronegativity Variance (Δχ)**: $\Delta\chi = \sqrt{\sum c_i (\chi_i - \bar{\chi})^2}$
    *   **VEC**: $\text{VEC} = \sum c_i \text{VEC}_i$
    *   **Mixing Entropy (ΔS_mix)**: $\Delta S_{mix} = -R \sum c_i \ln c_i$
    *   **Melting Temp Variance**: Similar to δ but using $T_m$.
*   **Physical Coupling Note**: Descriptors like Entropy and VEC may be physically correlated in stable single-phase alloys. The plan acknowledges this and frames results as **associational only**. If the dataset is biased towards stable single-phase alloys, descriptors may be collinear by definition. The permutation test measures marginal contribution in the presence of correlation, not independent causal effect.

### 2. Model Training (FR-004, FR-005)
*   **Algorithms**: Random Forest (a configured ensemble of decision trees), Gradient Boosting (a moderate ensemble of trees), OLS Linear Regression.
*   **Validation**: 5-fold Cross-Validation (seed=42).
*   **Stratification Strategy**: Yield Strength (continuous) is binned into **quartiles (4 bins)** for stratified splitting to ensure balanced distribution of low/high strength alloys in train/test sets.
*   **Evaluation**: Stratified 80/20 hold-out test set (seed=42).
*   **Metrics**: $R^2$, MAE, RMSE.

### 3. Statistical Validation (FR-006, FR-007, FR-008, FR-009, FR-011)
*   **VIF Calculation**: Calculated for all 5 descriptors. If VIF > 10, the descriptor is **flagged as collinear** but **NOT excluded** from testing.
*   **Permutation Importance**: 1000 permutations (seed=42) on **all 5 descriptors**.
*   **Multiple Comparison Correction**: **Bonferroni correction (k=5)** applied to the permutation p-values of **all 5 descriptors**.
    *   *Correction for Spec Contradiction*: The source spec (FR-007) suggests correcting only VIF < 10 descriptors. This plan implements correction on k=5 to avoid circular validation. The spec must be updated.
*   **Sensitivity Analysis**: Sweep $\alpha \in \{0.01, 0.05, 0.1\}$.
*   **Bootstrap Resampling**: 1000 resamples (seed=42) for 95% CI.

### 4. Power Analysis & Limitations
*   **Power Calculation**: For N=500 and 5 predictors, the detectable effect size (f²) at [deferred] power is approximately 0.05. This study is underpowered for small effects.
*   **Outcome**: If N < 500, the report will explicitly state "Reduced Statistical Power" and frame findings as "Directional Associations" rather than definitive hypothesis tests. The plan does not claim false precision for small N.

### 5. Compute Feasibility Strategy
*   **CPU-First**: All methods are feasible on -core CPU.
*   **No GPU Required**: The plan does not rely on deep learning.

## Decision Rationale
*   **Why Single Source?** To satisfy Constitution II (Verified Accuracy) and avoid fabrication.
*   **Why k=5 Correction?** To avoid circular validation where the test set is defined by the test result (VIF).
*   **Why Quartile Stratification?** To ensure balanced representation of the continuous target variable.