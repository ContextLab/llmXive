# Research: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

## Dataset Strategy

The project relies exclusively on the verified dataset listed in the `# Verified datasets` block.

| Dataset Name | Description | Source URL (Verified) | Usage |
| :--- | :--- | :--- | :--- |
| **GFA-D2 Pilot** | Experimental Metallic Glass compositions with critical cooling rates ($R_c$). | `https://huggingface.co/datasets/GFA-D2/pilot_flags/resolve/main/data.csv` | Primary training and validation data (FR-001). |

**Dataset Verification & Schema Check**:
- **Required Variables**: The spec requires elemental composition (fractions) and a continuous target variable ($log_{10}(R_c)$).
- **Verification Step**: Upon download, the ingestion script (`01_ingest_and_engineer.py`) MUST perform a strict schema check:
  1. Verify the presence of a column named `critical_cooling_rate`, `Rc`, or `log_Rc`.
  2. Verify the column contains continuous numeric values (not binary flags).
  3. Verify the column has a range of values (not constant).
- **Fallback/Failure**: If the dataset is binary-only (e.g., only `is_glass` flag) and lacks a continuous $R_c$ column:
  - The script MUST log a critical error: "Dataset lacks continuous critical cooling rate target. Regression task impossible."
  - The script MUST exit with code 1.
  - *Note*: No verified fallback URL exists in the `# Verified datasets` block. The pipeline halts if the primary dataset is insufficient.

## Feature Engineering Strategy

**Physics-Based Descriptors (FR-002)**:
The system will compute descriptors using `pymatgen` to ensure physical consistency.
1.  **Elemental Properties**:
    -   **Atomic Radius ($r$)**: Covalent or metallic radius (Å).
    -   **Electronegativity ($\chi$)**: Pauling scale.
    -   **Valence Electron Count (VEC)**: Raw count per element (required by FR-002).
        -   *Implementation*: Per-element VEC values are retrieved and used to compute interaction terms. The dataset stores the **weighted mean** VEC (`vec_mean`) and the **sum** of weighted VECs (`vec_raw` aggregate) for storage efficiency, but the calculation logic uses the full per-element vector.
    -   **VEC Mean**: Weighted mean of VEC.
2.  **Interaction Features**:
    -   **Atomic Size Mismatch ($\delta$)**: $\delta = \sqrt{\sum c_i (1 - r_i / \bar{r})^2}$.
    -   **Electronegativity Variance ($\Delta\chi$)**: Variance of electronegativity weighted by atomic fraction.
    -   **Weighted Mean VEC**: $\sum c_i \cdot VEC_i$.
    -   **Pairwise Size Mismatch**: For a ternary system (A, B, C), calculated as the sum of absolute differences for all unique pairs: $|r_A - r_B| + |r_B - r_C| + |r_C - r_A|$.
    -   **Triplet Interaction**: The variance of the atomic radii of the three specific elements in the system: $Var(r_A, r_B, r_C)$.
    -   **Specific Pair Descriptors**: For ternary systems, specific pairwise interaction terms (e.g., $r_{A} - r_{B}$) are calculated to capture local atomic environments beyond global means.
3.  **Normalization**: All features will be scaled using `StandardScaler` to zero mean and unit variance before model training.

**Handling Unknown Elements**:
If a composition contains an element not found in `pymatgen`'s `Element` database, the row will be excluded from the training set, and a warning will be logged (US-1, Acceptance Scenario 3).

## Model Strategy

**Algorithms (FR-003)**:
1.  **Random Forest Regressor**: Robust to non-linearities and feature interactions.
2.  **Gradient Boosting Regressor**: High predictive accuracy for tabular data.
3.  **Bootstrapped Ensemble**: Multiple independent Random Forest models trained on bootstrap samples to estimate prediction variance for confidence intervals (FR-007).

**Validation Strategy (FR-004)**:
-   **Method**: Leave-One-Cluster-Out (LOCO).
-   **Cluster Definition**: Groups based on the primary metallic element (e.g., Zr-based, Cu-based, Fe-based).
-   **Rationale**: Random splits may leak chemical family information, leading to over-optimistic performance. LOCO tests the model's ability to generalize to entirely new chemical families.
-   **Metric**: Mean Absolute Error (MAE) and $R^2$.

**Statistical Rigor & Heteroscedasticity (FR-010)**:
-   **Residual Analysis**: Post-training, residuals will be tested for heteroscedasticity using the Breusch-Pagan test (via `statsmodels`).
-   **Remediation (Non-Circular)**: If $p < 0.05$:
  1.  **Multivariate Binning**: Use K-Means clustering (k=10) on the **full feature vector** (all descriptors) to group samples with similar physical environments.
  2.  **Estimate Local Variance**: Calculate the variance of residuals within each cluster ($\sigma^2_{cluster}$).
  3.  **Generate Weights**: Assign weights to each sample inversely proportional to the variance of its cluster ($w_i = 1 / \sigma^2_{cluster}$).
  4.  **Retrain**: Retrain the model using these weights (via `sample_weight` in scikit-learn) with L2 regularization.
  5.  **Save**: Save the retrained model as `best_model_weighted.pkl`.

**Domain of Applicability (FR-009)**:
-   **Method**: Conformal Prediction.
-   **Calibration Set**: The **validation folds** from the LOCO cross-validation process will be used as the calibration set.
-   **Implementation**: Using the LOCO validation residuals to calibrate a prediction interval. Candidates falling outside the calibrated interval (high extrapolation risk) will be flagged.

## Feature Importance Analysis (SC-002)

-   **Method**: SHAP (SHapley Additive exPlanations).
-   **Implementation**: After model selection, SHAP values will be computed for the best model on the test set.
-   **Output**: A summary plot and a ranked list of the top 5 features.
-   **Script**: `04_analyze_feature_importance.py`.

## Screening Strategy (FR-005, FR-006)

1.  **Combinatorial Generation**: Generate all unique ternary combinations from the 30 specified abundant elements.
    -   *Constraint*: Combinations where fractions do not sum to unity (within tolerance) are excluded.
    -   *Estimation*: $N=30$ elements $\rightarrow \binom{30}{3} = 4060$ unique ternary compositions.
2.  **Novelty Check (SC-003)**:
    -   Compare generated candidates against the **training set** and the **Materials Project** database (via `pymatgen`).
    -   **Limitation**: No automated API exists for "existing literature" of metallic glasses. Novelty is defined as absence from these programmatic sources. The `verification_requests.json` is designed to be manually cross-referenced with literature by the user.
    -   If a candidate composition matches a known entry in these sources, it is marked `novelty: false`. Otherwise, `novelty: true`.
3.  **DoA Construction**:
    -   Calculate Mahalanobis distance of the candidate's feature vector from the **training set** feature distribution.
    -   If distance > 95% confidence ellipsoid threshold, flag as `high_extrapolation_risk`.
    -   **Exclusion Rule**: Candidates flagged as `high_extrapolation_risk` are **immediately excluded** from the final Top 10 list, regardless of their predicted value.
4.  **Prediction**: Predict $log_{10}(R_c)$ using the best model.
5.  **Uncertainty Quantification**:
    -   Apply Conformal Prediction to generate the prediction interval $[lower, upper]$.
    -   Calculate the **Conservative Score**: `predicted_mean` - 1.645 * (`upper` - `lower`). This score penalizes high uncertainty.
6.  **Filtering & Ranking**:
    -   **Threshold**: Set to the **10th percentile** of the training set's $log_{10}(R_c)$ values (data-driven).
    -   **Fallback**: If the 10th percentile yields zero candidates, fall back to the **25th percentile** and log a warning.
    -   **Ranking**: The final rank is determined **solely** by the **Conservative Score** (ascending order). Candidates with `high_extrapolation_risk` are excluded.
7.  **Output**: Top 10 candidates (or fewer) with `verification_requests.json` generation.

## Compute Feasibility Analysis

-   **Dataset Size**: Expected < 1,000 rows. Fits easily in RAM.
-   **Feature Engineering**: Pymatgen lookups are fast for <1,000 rows.
-   **Model Training**: Random Forest and Gradient Boosting on <1,000 rows with $\le 30$ hyperparameter combinations will complete in minutes on CPU.
-   **Screening**: Predicting a large number of candidates is trivial for tree-based models.
-   **Memory**: Estimated peak usage < 1GB.
-   **Time**: Total pipeline estimated < 1 hour.
-   **Conclusion**: The plan is fully feasible on the GitHub Actions free-tier (limited CPU, 7GB RAM, 6h limit).