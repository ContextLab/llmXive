# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Problem Statement

The research question asks: "How does the concentration of specific alloying elements (e.g., Cu, Mg, Si, Zn) influence the Poisson's ratio of monolithic aluminum alloys?"

This is a regression problem involving compositional data. The input features (elemental atomic fractions) are constrained to sum to 1.0 (the closure problem). Standard regression techniques fail on such data due to spurious correlations. The solution requires **Isometric Log-Ratio (ILR)** transformation to map the data to an unconstrained Euclidean space before applying a **Random Forest** regressor.

## Dataset Strategy

### Data Source Verification

Per the project constraints and the "Verified datasets" block provided, the following source is available and verified:

-   **Dataset**: `materials/alloy-elastic`
-   **Source**: HuggingFace Datasets
-   **URL**: `https://huggingface.co/datasets/materials/alloy-elastic`
-   **Content**: Aluminum alloy compositional data (Cu, Mg, Si, Zn, Mn, Al) and elastic properties (Poisson's ratio, Young's modulus).

**Critical Finding**: The previously assumed NIST/Materials Project APIs are unverified in the provided context and may require authentication or yield insufficient data. The plan now relies exclusively on the verified HuggingFace dataset `materials/alloy-elastic` to ensure reproducibility and data availability on the CI runner.

**Resolution Strategy**:
1.  **Primary Path**: Fetch data from `materials/alloy-elastic` using the `datasets` library.
2.  **Fallback**: If the dataset yields < 50 valid entries, the pipeline halts with a clear error message. No synthetic data or alternative unverified sources will be used.
3.  **No Fabrication**: We will not use LLM/CUDA datasets as substitutes, as they contain no relevant physical properties. We will not synthesize data.

### Data Availability & Feasibility

-   **HuggingFace `materials/alloy-elastic`**: Publicly accessible, programmatic download. Contains elastic constants for many alloys.
-   **Feasibility**: If the dataset yields < 50 entries with complete data, the project will be flagged as "Data Insufficient" and halted. This is a hard constraint defined in the Spec.

## Statistical Rigor & Methodology

### Compositional Data Analysis (CoDA)
-   **Problem**: Atomic fractions $x_i$ sum to 1. A change in one element forces a change in others (collinearity).
-   **Solution**: **Isometric Log-Ratio (ILR)** transformation.
    -   Maps the $D$-part composition to $D-1$ real coordinates.
    -   Preserves distances and geometry of the simplex.
    -   Eliminates the unit-sum constraint, allowing standard ML models (Random Forest) to operate validly.

### Model Selection: Random Forest
-   **Why**: Non-linear relationships are expected between composition and elastic properties. RF handles high-dimensional interactions well and provides feature importance.
-   **Constraints**: CPU-only. RF is highly parallelizable but on 2 cores, we limit `n_estimators` to 100-200 to ensure runtime < 1 hour.

### Validation Strategy
-   **Repeated Cross-Validation**: **Repeated 5-Fold CV** (5 repeats) to estimate generalization error and provide confidence intervals.
-   **Metric**: Mean Absolute Error (MAE) on Poisson's ratio (unitless, typical range of approximately one-third to slightly above one-third).
-   **No Single Hold-out**: A single 80/20 split is avoided due to high variance in small datasets.

### Causal Framing
-   **Observational Nature**: The data is observational (alloys were made by humans with specific intents, not randomized).
-   **Constraint**: We **cannot** claim that adding Cu *causes* a change in Poisson's ratio.
-   **Framing**: All results will be described as **associational (not causal)**. "Higher Cu content is associated with X change in Poisson's ratio."

### Collinearity Diagnostics
-   **VIF**: Variance Inflation Factor will be calculated on the *raw* (non-ILR) composition.
-   **Interpretation**: Due to the closure problem (sum=1), VIF on raw features is mathematically guaranteed to be very high (often infinite). This is **expected** and serves as a diagnostic to confirm the necessity of ILR transformation, not as a data quality flag.
-   **Threshold**: VIF > 5 is expected and confirms the closure problem.

### Feature Importance Interpretation
-   **Challenge**: Random Forest feature importance (Gini gain) cannot be mathematically back-transformed from ILR space to the original simplex.
-   **Solution**: Use **Permutation Importance** on the ILR-transformed features. This measures the drop in model performance when a feature is randomly shuffled, providing a valid measure of contribution without requiring a back-transformation of coefficients.
-   **Reporting**: Elements are ranked by the magnitude of their Permutation Importance scores.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **ILR Transformation** | Mandatory for compositional data. Log-ratio transforms (CLR) leave a singularity; ILR removes it. |
| **Random Forest** | Robust to outliers, handles non-linearities, no need for feature scaling, provides built-in importance. |
| **CPU-Only** | Dataset size (<1000 rows) is small enough for CPU. No GPU needed. |
| **Associational Framing** | Strict adherence to the observational nature of materials data. Prevents scientific overreach. |
| **Halt on <50 Samples** | Ensures statistical power. Repeated 5-fold CV with <10 samples/fold is unreliable. |
| **VIF on Raw Features** | Used as a diagnostic to demonstrate the closure problem (expected high VIF), justifying ILR. |
| **Permutation Importance** | Valid method for interpreting RF importance in ILR space; avoids invalid back-transformation. |
| **Repeated CV** | Reduces variance in performance estimates for small datasets compared to a single split. |