# Research: Predicting the Impact of Composition on the Density of Metallic Glasses

## 1. Scientific Context & Hypothesis

### 1.1 Background
Metallic glasses (amorphous alloys) possess unique mechanical and physical properties due to their disordered atomic structure. Predicting their bulk density is critical for lightweight structural applications. Traditional prediction methods rely on the **Linear Mixing Rule** (volume additivity), which assumes the density of an alloy is the weighted sum of its constituent elements' densities. However, amorphous structures often exhibit packing inefficiencies or excess free volume that cause deviations from this linear baseline.

### 1.2 Research Question
Can compositional descriptors derived from atomic properties (radius, electronegativity, packing efficiency) predict the *residual* density (deviation from the linear mixing rule) of metallic glasses more accurately than mass-based descriptors alone?

### 1.3 Hypothesis
The inclusion of non-linear atomic packing descriptors—specifically **atomic radius mismatch** and a **packing efficiency proxy**—significantly improves the prediction of residual density compared to a **Mass-Only Baseline Model** (using only mean atomic mass).

## 2. Dataset Strategy

### 2.1 Data Sources
The project targets public repositories containing metallic glass compositions and densities. Per the spec, the system attempts to fetch from:
1.  **Primary**: Zenodo (Metallic Glass Database)
2.  **Secondary**: Materials Cloud

*Note: As of the current verification, specific direct URLs for a "Metallic Glass Density" dataset were not present in the provided "# Verified datasets" block. Consequently, the implementation **must** rely on the spec's fallback mechanism: attempting the Zenodo/Materials Cloud URLs defined in `code/data/download.py`. If these fail or yield <50 rows, the system **must** switch to **Pipeline Validation Mode** generating synthetic data.*

### 2.2 Synthetic Data Strategy (Pipeline Validation Mode)
**CRITICAL LIMITATION**: Synthetic data is generated **ONLY** to validate the pipeline code path. It is **NOT** used for scientific hypothesis testing.
- **Generation Logic**: Linear Mixing Rule + Gaussian Noise ($\sigma=0.05$ g/cm³).
- **Composition**: Random mass fractions for common metallic glass formers (Zr, Cu, Ti, Ni, Fe, Pd) ensuring sum=1.0.
- **Dominant Element Distribution**: If real data is available, the synthetic data mimics the dominant element frequencies; otherwise, a uniform distribution is used.
- **Row Count**: $\ge$ 100 rows.
- **Scientific Validity**: Because the synthetic residuals are pure noise (by definition of the generation rule), **no scientific conclusions** regarding packing efficiency or radius mismatch can be drawn from a synthetic run. Success in this mode is defined solely by the successful execution of the pipeline and the generation of a valid report structure, not by model performance metrics (MAE/R²).

### 2.3 Data Variables
| Variable | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition` | Map | Mass fractions of elements (e.g., `{"Zr": 0.6, "Cu": 0.4}`) | Dataset / Synthetic |
| `bulk_density` | Float | Target variable (g/cm³) | Dataset / Synthetic |
| `mean_atomic_mass` | Float | Weighted mean atomic mass | Calculated (`mendeleev`) |
| `mean_atomic_radius` | Float | Weighted mean atomic radius (atomic fractions) | Calculated (`mendeleev`) |
| `radius_mismatch` | Float | Standard deviation of atomic radii | Calculated |
| `packing_efficiency` | Float | Non-linear geometric proxy | Calculated (Spec Formula) |
| `electronegativity_var`| Float | Variance of electronegativity | Calculated (`mendeleev`) |

## 3. Methodology

### 3.1 Feature Engineering
1.  **Normalization**: Convert all elemental symbols to standard IUPAC format.
2.  **Baseline Calculation**: Compute $\rho_{baseline} = \sum (w_i \times \rho_{element\_i})$.
3.  **Residual Target**: $y_{target} = \rho_{actual} - \rho_{baseline}$.
4.  **Descriptor Calculation**:
    -   **Atomic Fractions**: Convert mass fractions to atomic fractions for radius-based calculations to mitigate collinearity.
    -   **Packing Efficiency Proxy**: $PE = 1 - (\sigma_r / r_{mean})^2 \times (1 - 0.5 \times (\Delta r / r_{mean})^2)$.
    -   **Guard Clause**: If $\sigma_r = 0$, $PE = 1.0$.
    -   **Literature Basis**: While this specific PE formula is an ad-hoc geometric proxy and not a standard literature invariant (which typically use atomic size difference $\delta$), it serves as a valid test case for non-linear packing effects. Sensitivity analysis will be performed to ensure the model is not fitting noise from this specific functional form.

### 3.2 Model Training & Validation
-   **Algorithm**: Gradient Boosting Regressor (LightGBM).
-   **Input**: Compositional descriptors (Mean Mass, Radius Mismatch, PE, etc.).
-   **Target**: Residual Density ($\rho_{actual} - \rho_{baseline}$).
-   **Validation Strategy**: **Group K-Fold (k=5)** using the **Dominant Element** as the group identifier.
    -   *Rationale*: Stratified K-Fold risks data leakage if the dominant element family correlates with the residual. Group K-Fold ensures the model is tested on unseen element families, providing a rigorous test of generalizability.
-   **Hardware**: CPU-only (LightGBM default).

### 3.3 Evaluation Metrics & Hypothesis Testing
-   **Primary**: Mean Absolute Error (MAE) on residual density. Target: $\le 0.1$ g/cm³.
-   **Baseline Comparison**: The model's performance is compared against a **Mass-Only Baseline Model** (Linear Regression using only `mean_atomic_mass` to predict residuals).
    -   *Rationale*: The Spec's definition of "Baseline" as the Linear Mixing Rule (which predicts zero residual) is tautological. The true scientific test is whether the *Full Model* (Packing + Mass) significantly outperforms the *Mass-Only Model*.
-   **Statistical Test**: Paired t-test on the MAE residuals between the Full Model and the Mass-Only Model ($p < 0.05$).
-   **Secondary**: R-squared ($R^2$) improvement of Full Model over Mass-Only Model.
-   **Robustness**: Sensitivity analysis with Gaussian noise ($\sigma \in \{0.01, 0.05, 0.1\}$).

### 3.4 Interpretability & Distinct Findings
-   **SHAP Values**: To rank feature importance and specifically compare the contribution of `radius_mismatch` vs `mean_atomic_mass`.
-   **Partial Dependence Plots (PDP)**: To visualize the non-linear relationship between packing efficiency and residual density.
-   **Constitution VII Compliance**: If MAE > 0.1, the report **MUST** explicitly analyze the variance explained by radius mismatch as a distinct finding, using SHAP comparison and PDPs, even if the screening threshold is not met.

## 4. Feasibility & Constraints

-   **Compute**: The pipeline is designed for the GitHub Actions free tier (limited CPU and RAM). LightGBM on tabular data with <10k rows is CPU-tractable.
-   **Data Access**: If Zenodo/Materials Cloud links are dead, the synthetic fallback ensures the pipeline remains functional and testable (code path validation only).
-   **Collinearity**: The use of atomic fractions for radius descriptors and residual targets for training explicitly addresses the collinearity between mass and radius.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Residual Target** | Isolates the specific scientific question (non-linear packing) from the dominant linear mass effect. |
| **Synthetic Fallback** | Ensures reproducibility and CI/CD validation even when real-world data is inaccessible or sparse. **No scientific claims are made from this mode.** |
| **Atomic Fractions** | Required for physically meaningful radius calculations; mass fractions would bias the result. |
| **LightGBM** | Fast, CPU-efficient, and provides built-in feature importance for SHAP integration. |
| **Group K-Fold** | Prevents data leakage and ensures the model generalizes to unseen element families. |
| **Mass-Only Baseline** | Provides a rigorous, non-tautological comparison to validate the added value of packing descriptors. |