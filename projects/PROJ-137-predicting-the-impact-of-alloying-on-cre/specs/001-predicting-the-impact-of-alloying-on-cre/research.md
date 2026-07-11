# Research: Predicting the Impact of Alloying on Creep Resistance via Public Data

## 1. Problem Statement & Motivation

Creep resistance in high-temperature alloys is a critical property for aerospace and energy applications. While microstructural data (grain size, precipitates) is known to be influential, it is often difficult to predict *a priori*. This study investigates whether **thermodynamic descriptors** (mixing enthalpy, atomic radius mismatch), derived solely from elemental composition, can serve as effective predictors for creep rupture time, offering a "composition-only" predictive ceiling.

The core hypothesis is that physics-informed feature engineering (transforming raw weight% into thermodynamic properties) captures non-linear interactions better than raw composition, even if the information source is the same. This study distinguishes between **Methodology Validation** (using synthetic data to verify the pipeline detects known physical laws) and **Scientific Discovery** (using real data to find new correlations).

## 2. Dataset Strategy

### 2.1 Primary Source: Synthetic Data (Methodology Validation)
Due to the unverified status of the NIMS Creep Data Center URL in the project's verified dataset list, the **primary execution path** is the generation of a synthetic dataset.

*   **Generation Logic**: The synthetic data generator enforces physical laws:
    *   **Arrhenius Dependence**: `log(t) = A + B/T` (Temperature dependence)
    *   **Power-Law Stress**: `t = C * sigma^-n` (Stress dependence)
    *   **Composition Effects**: Random sampling of elemental fractions with derived thermodynamic properties.
*   **Validation**: A "Physics Consistency Check" is performed immediately after generation. A baseline model trained on this synthetic data must achieve **R² > 0.8**. If not, the generator parameters in `config/synthetic_params.yaml` are adjusted, or execution halts.
*   **Statistical Targets**:
    *   Mean/SD of `rupture_time` within [deferred] of target distributions.
    *   Kolmogorov-Smirnov distance of composition distributions ≤ 0.05.

### 2.2 Secondary Source: NIMS Creep Data (If Verified)
If the NIMS source becomes verified and reachable:
*   **Source**: NIMS Creep Data Center (CSV/Parquet).
*   **Access**: Downloaded via `requests` with exponential backoff.
*   **Preprocessing**:
    *   Filter rows with missing `temperature`, `stress`, or `rupture_time`.
    *   **Duplicate Handling**: Average `rupture_time` for identical alloy/condition entries.
    *   **Thermodynamic Lookup**: Query Materials Project API for mixing enthalpy and atomic radius.
    *   **Exclusion Rule**: Entries with missing thermodynamic data are **excluded from BOTH models** (Thermodynamic and Composition-Only) to ensure a fair comparison on the intersection of valid data.

### 2.3 Materials Project Integration
*   **API**: `pymatgen`'s `MPRester`.
*   **Strategy**: Batch retrieval of unique alloy compositions.
*   **Rate Limiting**: Exponential backoff (up to 3 retries) for rate limits.
*   **Fallback**: If API fails for a specific entry, log as "unresolved" and exclude from the final dataset.

### 2.4 Verified Datasets Reference
*   **NIMS**: No verified URL found in the provided list. **Primary path is Synthetic.**
*   **Materials Project**: Requires API key; not a static dataset.
*   **SHAP**: No verified source found. Library used for analysis.

## 3. Methodology

### 3.1 Feature Engineering
1.  **Composition Parsing**: Convert raw strings (e.g., "Ni-10Cr-5Al") to normalized atomic fractions.
    *   Sort elements alphabetically.
    *   Round stoichiometry to 2 decimals.
    *   Convert weight% to atomic% if necessary.
2.  **Thermodynamic Descriptors**:
    *   **Mixing Enthalpy ($\Delta H_{mix}$)**: Calculated using `pymatgen` thermodynamics.
    *   **Atomic Radius Mismatch ($\delta$)**: Calculated as the standard deviation of atomic radii weighted by atomic fraction.
    *   **Solid-Solution Strengthening**: Estimated based on elemental fractions.
3.  **Baseline Features**: Raw elemental weight percentages (no derived features).

### 3.2 Modeling Strategy
*   **Algorithm**: Gradient Boosting Regressor (GBR) from `scikit-learn`.
*   **Validation**: **Nested Cross-Validation**.
    *   **Outer Loop**:
        *   If $N \ge 50$: 10-fold Stratified by **Temperature Range**.
        *   If $N < 50$: Repeated 5-fold (5 repeats).
    *   **Inner Loop**: Hyperparameter tuning (GridSearch/RandomizedSearch).
*   **Fair Comparison**: Both models (Thermodynamic vs. Composition-Only) are trained on the **exact same subset** of data (intersection of valid entries).

### 3.3 Statistical Analysis
*   **Metric**: R² and RMSE from Outer Loop CV.
*   **Significance Testing**:
    *   **N < 20**: Bootstrap 95% Confidence Interval for the difference in RMSE.
    *   **20 ≤ N < 100**: Corrected Resampled t-test (Nadeau & Bengio) **AND** Sensitivity Analysis (sweeping cutoff over {0.01, 0.05, 0.1}).
*   **Interpretability**: SHAP (SHapley Additive exPlanations) to rank feature importance and determine direction of influence.

## 4. Statistical Rigor & Assumptions

*   **Multiple Comparisons**: The study compares exactly two models (Thermodynamic vs. Baseline). The Corrected Resampled t-test accounts for the dependence between folds.
*   **Power Limitation**: With $N < 100$, statistical power is low. The study explicitly frames results as **methodology validation** on synthetic data and **exploratory** on real data. No claims of definitive causal inference are made.
*   **Causal Assumptions**: The relationship is **associational**. The study does not claim that thermodynamic descriptors *cause* creep resistance, but that they are predictive.
*   **Collinearity**: Thermodynamic descriptors are derived from composition. The study does **not** claim independent effects of descriptors vs. composition; rather, it tests if the *transform* (feature engineering) improves model convergence/prediction.
*   **Measurement Validity**: Synthetic data validity is ensured via the Physics Consistency Check ($R^2 > 0.8$). Real data relies on the accuracy of the NIMS source and Materials Project API.

## 5. Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (multiple CPUs, sufficient RAM).
*   **Strategy**:
    *   No GPU/CUDA usage.
    *   Data subset to fit RAM (max N < 1000).
    *   `scikit-learn` GBR is CPU-tractable for small N.
    *   SHAP computation limited to `TreeExplainer` (fast for tree-based models).
*   **Runtime**: Estimated < 2 hours for full pipeline (including Nested CV).

## 6. Decision Rationale

*   **Synthetic Data First**: Chosen because the NIMS source is unverified. This ensures the project is runnable and testable in CI without external dependencies.
*   **Strict Intersection**: Excluding rows with missing thermodynamic data from *both* models prevents selection bias. If the thermodynamic model had more data, any performance gain could be attributed to data volume rather than feature quality.
*   **Stratification by Temperature**: Required by Constitution Principle VII to prevent leakage, as temperature is a dominant factor in creep.
*   **Nested CV**: Essential for small data to avoid overfitting during hyperparameter tuning.
