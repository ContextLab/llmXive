# Data Model: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

## 1. Entity Definitions

### 1.1 EBSD Sample
Represents a single measurement point or a small region from an EBSD scan.
-   **ID**: Unique identifier (string).
-   **Material**: Enum {`Al`, `Cu`, `Ni`}.
-   **Reduction_Percentage**: Float (0.0 to 80.0).
-   **Euler_Angles**: Tuple of 3 floats (phi1, Phi, phi2) in Bunge convention.
-   **Confidence_Index**: Float (0.0 to 1.0).
-   **Symmetry**: String (fixed: `FCC`).

### 1.2 Texture Descriptor
Aggregated scalar metrics derived from a set of EBSD Samples for a specific Material/Reduction combination.
-   **Sample_ID**: Reference to the group of EBSD Samples.
-   **Material**: Enum {`Al`, `Cu`, `Ni`}.
-   **Reduction_Percentage**: Float.
-   **Volume_Fraction_Brass**: Float (0.0 to 1.0).
-   **Volume_Fraction_Copper**: Float (0.0 to 1.0).
-   **Volume_Fraction_S**: Float (0.0 to 1.0).
-   **Volume_Fraction_Goss**: Float (0.0 to 1.0).
-   **Texture_Index**: Float (≥ 1.0).
-   **Mass_Balance_Check**: Boolean (True if sum of fractions ≈ 1.0).

### 1.3 Model Prediction
Output of the predictive model for a given input.
-   **Input_Material**: Enum.
-   **Input_Reduction**: Float.
-   **Predicted_Brass**: Float.
-   **Predicted_Copper**: Float.
-   **Predicted_S**: Float.
-   **Predicted_Goss**: Float.
-   **Predicted_Texture_Index**: Float.
-   **Confidence_Interval_Upper**: Float.
-   **Confidence_Interval_Lower**: Float.
-   **Is_Extrapolated**: Boolean.
-   **Residual_Variance_Contribution**: Float (percentage of unexplained variance).

## 2. Data Flow

1.  **Raw Input**: `data_synth_ebsd.zip` (from HuggingFace).
2.  **Pre-processed**: `ebsd_clean.parquet` (Filtered, Re-indexed).
3.  **Derived**: `texture_descriptors.parquet` (Aggregated metrics).
4.  **Model Output**: `predictions.parquet` (Model outputs with confidence intervals).

## 3. Constraints & Validations

-   **Symmetry**: All Euler angles must be re-indexed to `FCC` (m-3m) before aggregation.
-   **Confidence**: Points with `Confidence_Index < 0.1` are excluded from aggregation.
-   **Mass Balance**: $\sum \text{Volume Fractions} \in [0.99, 1.01]$.
-   **Range**: `Reduction_Percentage` must be within [0.0, 80.0] for interpolation; >80.0 or <0.0 triggers `Is_Extrapolated = True`.
