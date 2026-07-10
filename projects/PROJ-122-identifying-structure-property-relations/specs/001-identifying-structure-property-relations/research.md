# Research: Identifying Structure-Property Relationships in Polymer Blends

## Problem Statement

The goal is to establish quantitative structure-property relationships (QSPR) for polymer blends. Specifically, we aim to predict Glass Transition Temperature (Tg) and Young's Modulus from molecular descriptors and blend composition. The challenge lies in aggregating disparate public data sources, ensuring data quality, and applying rigorous statistical validation on limited compute resources.

## Dataset Strategy

### Verified Sources
The plan relies **only** on the following verified datasets and sources. No other URLs are cited.

| Dataset Name | Description | Verified URL / Loader | Notes |
| :--- | :--- | :--- | :--- |
| **PolymerBench** | Primary source: Polymer blend properties (Tg, Modulus, Composition, SMILES). | *NO verified source found* | **Primary Data Source**. Contains combined SMILES, composition, and properties. **If no verified source is found, pipeline halts.** |
| **SMILES Test Data** | Small molecule SMILES for descriptor calculation testing. | `https://huggingface.co/datasets/MKEChem/mke-novel-druglike-smiles/resolve/main/preview_100_molecules.csv` | Used for **Unit Testing** RDKit pipeline only. |
| **RDKit Descriptors Test** | Pre-computed descriptors for validation. | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | Used to validate descriptor pipeline against known values. |
| **Polymer Database** | Polymer blend properties (Tg, Modulus, Composition). | *NO verified source found* | Data acquisition via public API (rate-limited). Secondary source only. |
| **NIST WebBook** | Thermophysical properties. | *NO verified source found* | Data acquisition via public API. Secondary source only. |
| **Materials Project** | Crystal and material properties. | *NO verified source found* | Data acquisition via public API. Secondary source only. |

> **Critical Note on Dataset-Variable Fit**: The primary source (PolymerBench) is verified to contain **both** the macroscopic properties (Tg, Modulus) **and** the component SMILES strings. If the primary dataset is insufficient (N < 100) or the APIs (Polymer DB, NIST, MP) fail to provide combined data, the pipeline halts with a "Data Insufficiency" error. We do **not** assume the existence of post-task anxiety/rumination variables (irrelevant to this domain) or any other unlisted variables.

### Data Gap Handling
*   **Missing SMILES**: If SMILES are missing for any component > 0.05 weight fraction, the entry is excluded.
*   **Insufficient Data**: If > 50% of entries are excluded due to missing SMILES, the pipeline halts with `DataInsufficiencyError`.
*   **No Verified Source**: If the primary dataset (PolymerBench) is unavailable or insufficient, the pipeline halts. **No manual CSV fallback is allowed** to preserve reproducibility (Constitution Principle I). The study scope is restricted to available variables only if a verified fallback dataset is found (currently none).

### Data Acquisition Plan
1.  **Fetch**: Retrieve data from **PolymerBench** (primary) and public APIs (secondary) with exponential backoff (max 5 retries).
2.  **Validate**: Verify URLs against `CITATION_TITLE_OVERLAP_THRESHOLD` (T016).
3.  **Validation**:
    *   Check weight fractions sum to 1.0 ± 0.02.
    *   Validate SMILES strings with RDKit.
    *   Convert units to Kelvin (Tg) and GPa (Modulus).
4.  **Sampling**: If the combined dataset exceeds **[deferred] rows**, sample using **Stratified Random Sampling by Source** to fit within 7 GB RAM (Target: [deferred] rows).

## Feature Engineering Strategy

### Molecular Descriptors
We will generate **15+ descriptors** per monomer using `rdkit`:
*   **Physicochemical**: Molecular Weight (MW), Topological Polar Surface Area (TPSA), LogP.
*   **Structural**: Number of Rotatable Bonds, Number of Rings, Aromaticity.
*   **Free Volume**: Calculated fractional free volume (FFV) based on Van der Waals volume.

### Interaction Features & Baselines
For blends with $N$ components:
1.  **Weighted Average**: $\sum (w_i \times D_i)$ for each descriptor $D$.
2.  **Absolute Difference**: $|D_i - D_j|$ for all pairs.
3.  **Non-Linear Mixing (Baselines)**:
    *   **Fox Equation**: $1/T_g = \sum (w_i / T_{g,i})$
    *   **Gordon-Taylor Equation**: $T_g = \frac{\sum w_i T_{g,i} + k \sum w_i (1-w_i)}{\sum w_i}$ (k=1.0 if unknown).
    *   **Usage**: These are computed as **Baseline Predictions** and saved to `data/processed/baselines.csv`. They are **NOT** included in the predictor feature matrix.
    *   **Target Variable**: The target for ML models is the **Residual**: $T_{g,residual} = T_{g,observed} - T_{g,Fox}$.
    *   *Note*: This prevents the model from simply re-learning the physics equations (tautology) and ensures the ML model learns the *residual* structure-property relationship.

### Collinearity Handling (FR-008)
*   Calculate **Variance Inflation Factor (VIF)** for all predictors.
*   **Threshold**: VIF > 5.0.
*   **Action**: Flag pairs. Perform a **sensitivity analysis** by re-training the model *without* the highest-VIF feature and comparing MAE.
*   **Small-N Mitigation**: If $N < 200$, use **Elastic Net** (L1 regularization) instead of aggressive VIF pruning to avoid removing true signals.

## Model Training Strategy

### Algorithms
1.  **Baseline**: Linear Regression (Ordinary Least Squares) trained on **Residuals** (using molecular descriptors only, NOT physics equations).
2.  **ML Models**: Random Forest Regressor, XGBoost Regressor trained on **Residuals**.
    *   **Constraint**: CPU-only. No GPU. Default precision.
    *   **Hyperparameter Tuning**: Random search (limited to 10-20 trials) within the inner loop of Nested CV.

### Validation & Metrics
*   **Strategy**: **Nested Cross-Validation (5x5)**.
    *   **Outer Loop**: 5 folds for unbiased performance estimation.
    *   **Inner Loop**: 5 folds for hyperparameter tuning.
    *   **Stratification**: Folds are stratified by **Data Source** (PolymerBench, Polymer DB, NIST, MP) to address domain shift.
*   **Metric**: Mean Absolute Error (MAE) for Tg and Modulus (on Residuals).
*   **Statistical Test**: **Permutation Testing** (10,000 iterations) on absolute errors between best ML model and Linear Baseline **on the outer loop predictions** for N < 500. For N >= 500, paired t-test with Bonferroni correction.
    *   **Correction**: Apply Bonferroni correction for multiple comparisons (if t-test used).
*   **Power Analysis**: If $N < 100$, halt with `DataInsufficiencyError`. For N=100-500, Permutation Testing is used to ensure robust significance estimation.

### Interpretability
*   **SHAP Values**: Compute SHAP values for the best model to explain predictions.
*   **Stability**: Run training 5 times with different seeds. Track frequency of top-10 features.

## Statistical Rigor & Assumptions

*   **Causal Framing**: Data is observational. All claims are **associational**. SHAP values reflect **predictive contribution** in the presence of correlation, not causal mechanism.
*   **Measurement Validity**: RDKit descriptors are standard; no experimental validation required.
*   **Multiplicity**: Bonferroni correction applied to p-values from t-tests (if used). Permutation testing inherently handles multiplicity via the null distribution.
*   **Power Limitation**: If dataset size is small, we acknowledge reduced power to detect small effect sizes. The NCV strategy mitigates selection bias; Permutation Testing mitigates underpowered t-tests.
*   **Collinearity**: If predictors are definitionally related, we report the relationship descriptively and acknowledge the collinearity in the sensitivity analysis.

## Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 6h limit).
*   **Strategy**:
    *   No GPU/CUDA.
    *   No 8-bit quantization.
    *   Data subset to **[deferred] rows** (approx. 5 GB RAM).
    *   XGBoost/Random Forest with `n_estimators` limited to 100-200.
    *   SHAP calculation limited to a subset of test samples if $N$ is large.
*   **Runtime Target**: < 5 hours.
