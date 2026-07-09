# Research: Predicting the Impact of Alloying on Creep Resistance via Public Data

## 1. Problem Statement & Hypothesis

**Problem**: Predicting the creep resistance (rupture time) of superalloys is critical for high-temperature applications. While composition is a primary driver, the relationship is non-linear and influenced by complex interactions.
**Hypothesis**: Physics-informed thermodynamic descriptors (mixing enthalpy, atomic radius mismatch), derived from elemental composition using computational chemistry principles, provide a statistically significant predictive advantage over raw elemental **Atomic%** fractions (and their polynomial transforms) when modeling creep resistance.
**Null Hypothesis**: There is no significant difference in out-of-sample R² between a model using thermodynamic descriptors and a baseline model using raw Atomic% fractions (with or without polynomial features).

## 2. Dataset Strategy

The project relies on the **NIMS Creep Data Center** dataset for experimental rupture times and the **Materials Project** for thermodynamic properties. However, given the lack of a verified URL for the specific NIMS Creep dataset in the provided block, the **Synthetic Fallback** is the primary execution path.

| Dataset | Source URL (Verified) | Usage | Access Method |
| :--- | :--- | :--- | :--- |
| **NIMS Creep Data** | *None verified in prompt block* | Experimental rupture time, temperature, stress, composition string. | **Primary Execution Path**: If no verified URL exists, trigger Synthetic Data Generation (FR-008) immediately. No attempt to fetch from unverified URLs. |
| **Materials Project** | API via `MPRester` (No direct URL, requires API Key) | Validation of elemental properties; **NOT** direct source of mixing enthalpy/radius mismatch. | `pymatgen.ext.matproj.MPRester` (for validation) + `pymatgen` local elemental properties for descriptor calculation. |
| **Synthetic Fallback** | N/A (Generated locally) | Pipeline validation and primary data source if external sources fail. | `numpy.random` sampling based on NIMS statistics. |

**Critical Finding**: The prompt's "Verified datasets" block does **not** contain a verified URL for the actual **NIMS Creep Data Center**. The available URL (`Nimsi2613/MedQuad`) is a medical QA dataset, not creep data.
*Decision*: The plan strictly adheres to the **FR-001** requirement: If the specific NIMS Creep dataset is unreachable or the verified URLs do not match the schema, the system **MUST** generate a synthetic dataset matching the defined schema (FR-008). The research phase will **not** attempt to fetch from mismatched URLs. The **Synthetic Fallback is the primary execution path** given the lack of a verified creep dataset URL.

## 3. Methodology

### 3.1 Data Preprocessing
1.  **Parsing**: Raw composition strings (e.g., "Ni-10Cr-5Al") are parsed into elemental fractions.
2.  **Normalization**: Elements sorted alphabetically; stoichiometry rounded to 2 decimals; **weight% converted to Atomic% for ALL models** (Thermodynamic, Linear Baseline, Polynomial Baseline) to ensure unit consistency and isolate the effect of descriptors.
3.  **Feature Engineering**:
    *   **Raw Features**: Elemental **Atomic%** fractions (Composition-Only Baseline).
    *   **Polynomial Features**: Raw Atomic% fractions + Polynomial Features (degree 2) (Polynomial Baseline).
    *   **Thermodynamic Features**: Mixing Enthalpy ($\Delta H_{mix}$), Atomic Radius Mismatch ($\delta$), Average Atomic Radius ($\bar{R}$). Calculated using `pymatgen`'s **local elemental property database** (derived features, not direct MP API returns). The MP API is used only for validation of elemental properties if necessary, but descriptors are computed locally.
4.  **Handling Missing Data (Strict Intersection)**:
    *   Entries missing Temperature, Stress, or Rupture Time are dropped.
    *   Entries missing Thermodynamic data (MP API failure or calculation error) are **excluded from ALL models** (Thermodynamic, Linear, and Polynomial Baselines). This ensures the statistical test is performed on the exact same set of samples, preventing selection bias and ensuring paired testing validity.
    *   *Selection Bias Mitigation*: By enforcing Strict Intersection, the Baseline model is trained on the same subset of data as the Thermo model, preventing the Baseline from benefiting from a broader distribution of samples that the Thermo model cannot access.

### 3.2 Model Training Strategy
*   **Algorithm**: Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`).
*   **Validation**: Nested Cross-Validation.
    *   **Outer Loop**:
        *   If $N \ge 50$: 10-Fold Stratified (stratified by **joint Temperature-Stress quantiles**).
        *   If $N < 50$: Repeated 5-Fold (5 repeats).
    *   **Inner Loop**: Hyperparameter tuning (GridSearchCV) for `n_estimators`, `max_depth`, `learning_rate`.
*   **Models**:
    1.  **Thermo Model**: Trained on [Elemental Atomic% + Thermodynamic Descriptors].
    2.  **Linear Baseline**: Trained on [Elemental Atomic% Only].
    3.  **Polynomial Baseline**: Trained on [Elemental Atomic% + Polynomial Features (degree 2)]. *This is the primary comparator for physics isolation.*

### 3.3 Statistical Evaluation
*   **Metric**: Out-of-sample R² and RMSE.
*   **Significance Test**:
    *   If $N \ge 20$: **Corrected Resampled t-test** (Nadeau & Bengio correction) to account for overlapping folds. **Performed only on the strict intersection of samples.**
    *   If $N < 20$: **Bootstrap 95% Confidence Interval** for the difference in RMSE. No p-value reported.
*   **Success Criteria**: R² improvement $\ge 0.05$ for the Thermo Model over the **Polynomial Baseline**.

### 3.4 Interpretability
*   **SHAP Analysis**: `shap.TreeExplainer` applied to the best-performing model from the outer loop.
*   **Output**: Summary plot (beeswarm) and top 5 feature ranking.

## 4. Statistical Rigor & Constraints

*   **Multiple Comparisons**: Three primary models are compared (Thermo vs. Linear vs. Polynomial). Family-wise error correction (e.g., Bonferroni) will be applied if multiple pairwise tests are conducted.
*   **Power Justification**: Given the expected small sample size ($N < 100$), the project acknowledges limited statistical power. The use of Nested CV and the Corrected t-test is specifically chosen to maximize reliability in this regime. If $N < 20$, the study is explicitly labeled "Exploratory."
*   **Causal Inference**: The study is **observational**. Claims are strictly associational. No causal claims regarding alloying effects are made.
*   **Collinearity**: Elemental fractions sum to 1 (or [deferred]). This introduces perfect collinearity.
    *   *Mitigation*: The "Linear Baseline" will drop one element (e.g., the solvent) or use `OneHotEncoder` logic implicitly by using all but one. The Polynomial Baseline will apply the same logic. `GradientBoosting` handles collinearity by splitting on the most informative feature.
*   **Compute Feasibility**:
    *   **No GPU**: All models run on CPU.
    *   **Memory**: Data subset to < 1MB (text/numerical). `pymatgen` overhead is minimal for small N.
    *   **Time**: Nested CV with small N (<100) and shallow trees is computationally trivial (< 1 hour).

## 5. Risks & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **NIMS Data Unavailable** | Pipeline failure. | Trigger Synthetic Data Generation (FR-008) immediately. |
| **Materials Project API Limits** | Missing thermodynamic features. | Exponential backoff (3 retries); exclude specific entries from **ALL models** to ensure strict intersection. |
| **Small Sample Size (N < 20)** | Low statistical power. | Switch to Bootstrap CI; label as "Exploratory"; no p-values. |
| **Overfitting** | Inflated R² scores. | Strict Nested CV; no separate hold-out test set (data too small). |
| **Selection Bias** | Invalid statistical test. | **Strict Intersection** policy enforced: all models trained on identical sample sets. |
| **Unit Mismatch** | Confounded comparison. | **All models** use Atomic% fractions as the base representation. |
| **Non-Linearity Confound** | Tautology in feature gain. | Comparison is against **Polynomial Baseline** (Atomic% + Poly) to isolate physics-specific gain. |