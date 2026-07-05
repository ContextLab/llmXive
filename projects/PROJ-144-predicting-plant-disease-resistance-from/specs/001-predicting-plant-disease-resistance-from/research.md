# Research: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

## 1. Research Question & Hypothesis

**Question**: Can constitutive (pre-challenge) metabolite profiles predict plant disease resistance phenotypes?  
**Hypothesis**: A Random Forest classifier trained on pre-challenge metabolomic data will achieve a balanced accuracy > 75% on an independent hold-out set, indicating a significant predictive signal in the metabolome.  
**Null Hypothesis**: Predictive performance is no better than random chance (balanced accuracy ≈ 0.5), as confirmed by permutation testing (p < 0.05).

**Note on Causality**: As this study uses observational data from public repositories without randomization, all findings will be framed as **associational**. No causal claims regarding metabolites causing resistance will be made.

## 2. Dataset Strategy

The project relies on public metabolomics repositories. The spec explicitly identifies **Metabolomics Workbench** as the source.

### Verified Datasets & Sources
*The "Verified datasets" block provided in the prompt context contains no plant metabolomics data. The plan adheres to the constraint of not fabricating URLs.*

**CRITICAL GAP IDENTIFIED**: The provided verified list does not contain plant metabolomics data.
*   **Action**: The implementation will attempt to fetch data directly from **Metabolomics Workbench** (public API via HTTP requests) using study IDs that match the "plant disease" criteria.
*   **Constraint**: If no specific plant metabolomics dataset with the required variables (pre-challenge + resistance) is found in the public domain, the pipeline will **halt** with a "Data Unavailable" error. **No mock data will be used** to prevent false positives.
*   **Citation**: All datasets will be cited by their Metabolomics Workbench Study ID and the general source URL (https://www.metabolomicsworkbench.org/).

**Strategy**:
1.  **Primary Source**: Metabolomics Workbench (MW).
    *   *Access Method*: Direct HTTP requests to MW API or bulk download via MW study pages.
    *   *Selection Criteria*: Studies containing "plant", "disease", "challenge", "metabolome", "resistance".
    *   *Variable Check*: Must contain **pre-challenge** metabolite profiles and **disease-resistance** metadata for the same germplasm.
2.  **Fallback**: None. If data is unavailable, the study stops.

**Dataset Variable Fit Analysis**:
*   **Required Variables**: Pre-challenge metabolite intensities, Resistance labels (binary/ordinal), Germplasm ID, Assay method, Biological covariates (species, growth conditions).
*   **MW Availability**: MW hosts numerous plant metabolomics studies. The spec asserts that studies with *both* pre-challenge profiles and resistance labels exist.
*   **Risk**: If a specific study lacks *pre-challenge* data (only post-challenge), it must be excluded. The `validate_temporal.py` script must verify temporal metadata (FR-014).

## 3. Statistical Rigor & Methodology

### 3.1. Sample Size & Power
*   **Formal Power Analysis**: To detect a balanced accuracy of 0.75 against a null of 0.50 with Alpha=0.05 and Power=0.80, the minimum required sample size is approximately **N=128** (assuming effect size ~0.25).
*   **Constraint**: If the available dataset has N < 128, the study is **flagged as underpowered** for the specific hypothesis. The learning curve analysis (SC-004) will be performed, but the primary claim of "predictive signal" will be qualified as exploratory.
*   **Mitigation**: If N < 128, the report will explicitly state the power limitation and the risk of Type II error.

### 3.2. Multiple Comparison Correction & Feature Significance
*   **Correlation Analysis**: Pairwise correlations between individual metabolites and resistance labels are computed **only on the training fold** within the CV loop (or on the full dataset for exploratory visualization **only**, never for feature selection).
    *   *Correction*: Benjamini-Hochberg (BH) procedure to control False Discovery Rate (FDR) at ≤ 0.05 (FR-008, SC-002).
    *   *Threshold*: Significant correlations defined as |r| > 0.4, p < 0.01 (after BH correction).
    *   *Usage*: **Exploratory only**. These correlations are NOT used to filter features for the Random Forest model to avoid circular validation.
*   **Feature Significance**: To control for multiple testing in the Random Forest feature importance (the "Top 10" list), we will use **Permutation-Based Feature Significance**.
    *   *Method*: Permute the target labels a sufficient number of times to generate a null distribution of feature importance scores.
    *   *Threshold*: The threshold for significance is determined by a high percentile of the null distribution. Only features exceeding this threshold are reported as "significant".

### 3.3. Causal Inference & Assumptions
*   **Observational Nature**: Data is observational. No randomization of treatment.
*   **Claim Framing**: All results described as "associations" or "predictive signatures," never "causes."
*   **Confounding**:
    *   **Batch Effects**: Addressed via ComBat.
    *   **Biological Confounders**: Species, growth conditions, and soil type are extracted as covariates. These covariates are **residualized** from the metabolite intensities (or included in the ComBat design matrix) *before* model training to prevent them from being absorbed into the batch effect or driving the signal.

### 3.4. Predictor Collinearity
*   **Issue**: Metabolites in the same pathway are often highly correlated.
*   **Handling**:
    1.  **Model**: Random Forest handles collinearity internally for prediction.
    2.  **Interpretation**: **SHAP (SHapley Additive exPlanations)** values are calculated for top features (FR-012). SHAP is robust to collinearity and provides consistent feature attribution.
    3.  **Reporting**: If features are collinear, their individual importance is not claimed as independent; they are reported as a "signature" or "cluster" with stable SHAP values.

### 3.5. Permutation Testing
*   **Purpose**: Validate that model performance > chance.
*   **Method**: 1,000 permutations of the resistance labels (FR-007).
*   **Metric**: Compare observed balanced accuracy to the null distribution. p-value = (count(permutation_score >= observed_score) + 1) / (1000 + 1).

## 4. Computational Feasibility (CPU-Only)

*   **Hardware**: GitHub Actions Free Tier (multiple CPUs, sufficient RAM).
*   **Data Volume**: Metabolomics data is typically small (matrices < 1000 samples x 500 features). Fits easily in RAM.
*   **Model**: Random Forest (n_estimators=500, max_depth=10).
    *   *Feasibility*: RF is CPU-efficient. 500 trees on 50 features is trivial for 2 cores.
    *   *GridSearch*: Limited to `max_depth` (10-20) and `n_estimators` (500). Small search space.
*   **Permutation**: 1,000 permutations of a small RF model.
    *   *Time Estimate*: ~1-2 hours on CPU. Well within 6h limit.
*   **Libraries**: `scikit-learn` (CPU wheels), `pandas`, `numpy`, `shap`. No CUDA/GPU dependencies.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Random Forest** | Robust to non-linearity, handles mixed data types, provides feature importance, less prone to overfitting than deep nets on small data. |
| **ComBat + Covariate Residualization** | Standard for metabolomics batch correction; explicitly controls for biological confounders (Constitution Principle VI). |
| **Stratified 5-Fold CV** | Ensures class balance in folds; standard for small datasets. |
| **Permutation Testing** | Provides empirical p-value without distributional assumptions; required by Constitution Principle VII. |
| **SHAP Diagnostics** | Robust to collinearity and non-linearity; superior to VIF for tree-based models. |
| **Associational Framing** | Mandatory due to observational data (FR-011). |
| **No Deep Learning** | Overkill for small metabolomics data; high risk of overfitting; violates CPU constraints. |
| **No Mock Data** | Ensures validity; prevents false positives from synthetic data if real data is unavailable. |
