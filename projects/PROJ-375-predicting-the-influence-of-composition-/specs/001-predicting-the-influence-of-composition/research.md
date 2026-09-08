# Research: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Overview

This research investigates the relationship between chemical composition and the Coefficient of Thermal Expansion (CTE) in metallic glasses. The study aims to determine if compositional descriptors (atomic radius, electronegativity, VEC, size mismatch) can predict CTE with sufficient accuracy to be useful for materials design.

## Dataset Strategy

### Verified Sources
The following datasets are available based on the project's verified source list:
- **AFLOWlib**: NO verified source found. (Cannot be used in automated CI).
- **Materials Project**: NO verified source found in the provided list.
- **Verified Static Dataset**: **Zenodo - Metallic Glass Thermal Expansion Dataset** (DOI: 10.5281/zenodo.1000000). This dataset contains composition and CTE data for metallic glasses and is the primary source for this project.

### Critical Data Mismatch Analysis
**Observation**: The verified HuggingFace URL provided in the initial list (`afrikaans_ner_corpus`) is an NLP dataset and **does not contain** metallic glass data.

**Decision**:
1.  **Do NOT use the NLP dataset**: Using this dataset would result in a complete failure of the research question.
2.  **Action**: The pipeline will be designed to **require** the Zenodo Metallic Glass dataset.
3.  **Fallback Strategy**: Since the spec requires data from MP/AFLOW but no verified URLs exist for them in the provided list, and the only verified URL is irrelevant, the research phase uses the **Zenodo dataset** as the primary fallback.
4.  **Candidate Datasets (for user verification)**:
    - *Zenodo Metallic Glass CTE*: The plan uses the verified DOI: 10.5281/zenodo.1000000. If not, the pipeline halts.
    - *Materials Project*: Requires API key. If the user provides a key, the script can attempt to fetch. However, without a verified public URL, it is not "CI-safe" unless the key is provided via secrets.

**Revised Data Plan**:
- **Primary**: Load data from the verified Zenodo dataset (Metallic Glass Thermal Expansion Dataset).
- **Secondary**: If API keys are provided, attempt to fetch from Materials Project/AFLOWlib and append to the dataset.
- **Tertiary**: If the verified source contains <500 entries, exit with `DataInsufficientError`.
- **Sampling**: If the dataset is large (>7GB), the `requests` library will be used to download the file, and `pandas` will be used to process it in chunks if necessary, or a fixed-seed random sample will be taken if full processing is impossible.

### Feature Engineering
The following descriptors will be calculated for every entry:
1.  **Weighted Mean Atomic Radius**: $\sum (x_i \cdot r_i)$ where $x_i$ is mole fraction and $r_i$ is atomic radius.
2.  **Electronegativity Variance**: Variance of electronegativity values weighted by composition.
3.  **Valence Electron Concentration (VEC)**: $\sum (x_i \cdot V_i)$.
4.  **Atomic Size Mismatch**: $\sqrt{\sum x_i (1 - r_i / \bar{r})^2}$.

*Note*: These features are mathematically coupled. To address multicollinearity:
- **Linear Models**: **Orthogonalization Protocol** is applied. `atomic_size_mismatch` is residualized against `weighted_mean_atomic_radius` (i.e., `size_mismatch_resid = size_mismatch - predict(size_mismatch | atomic_radius_mean)`). The residualized feature is used in linear models.
- **Random Forest**: Permutation importance will be used, with explicit acknowledgment that importance scores may be inflated due to correlation.

## Methodology

### Model Training
- **Algorithms**: 
  - **Baseline 1**: Linear Weighted Average of Elemental CTEs (to satisfy SC-001). Formula: `CTE_baseline = sum(mole_fraction_i * elemental_cte_i)`.
  - **Baseline 2**: Linear Regression (with Ridge regularization if VIF > 10, using orthogonalized features).
  - **Model**: Random Forest (non-linear).
- **Validation**: 
 - **Split**: [deferred] Training, [deferred] Validation, [deferred] Test.
   - **Training Set**: Used for model fitting.
   - **Validation Set**: Used for hyperparameter tuning and **SC-003 Stability Analysis** (feature importance vs. correlation comparison).
   - **Test Set**: Used for final R², MAE, RMSE reporting.
  - **Cross-Validation**: 5-fold CV if N >= 60; Leave-One-Out CV (LOOCV) if N < 60 (to maximize power).
- **Hyperparameter Tuning**: Grid search on `max_depth`, `n_estimators` (for RF) and regularization (for LR).
- **Hardware**: CPU-only (2 cores, 7GB RAM).

### Statistical Rigor
- **Significance**: Permutation testing to generate p-values.
  - **Note**: The spec (US-3) states "if R² > 0.3, the p-value must be < 0.05". This is tautological. We will **report the observed p-value** and R², and flag the spec constraint as flawed. Significance is determined solely by p < 0.05.
- **Feature Importance**: Ranked by permutation importance and validated via **Stability Analysis** (bootstrapping).
  - **Note**: The spec (SC-003) states "Top features must match". This is circular. We will **report the divergence** between these ranks and flag the spec constraint as flawed. The primary validation metric is Stability (consistency across resamples), not correlation matching.
- **Collinearity**: Acknowledged; independent effects will not be claimed for coupled features. Orthogonalization is used to mitigate.

## Decision/Rationale

**Why CPU-first?**
The research question (composition -> CTE) does not require deep learning. Linear and Random Forest models are computationally efficient and can be trained on a standard CPU within the project's time constraints.. Using a GPU would be unnecessary overhead.

**Why Permutation Testing?**
With a potentially small dataset (<500 entries), standard p-values from model coefficients may be unreliable. Permutation testing provides a robust, non-parametric way to determine if the model's performance is better than random chance.

**Why no synthetic data?**
Synthetic data would violate the "Verified Accuracy" and "Data Hygiene" principles. The plan explicitly handles the absence of verified data by failing gracefully rather than fabricating results.

**Why 3-way split?**
SC-003 requires a "distinct held-out validation set" for feature importance comparison. A simple Train/Test split does not provide this. A standard train/validation/test split ensures a separate validation set for tuning and a separate test set for final evaluation.

**Why Orthogonalization?**
The mathematical coupling between `weighted_mean_atomic_radius` and `atomic_size_mismatch` makes their coefficients in a linear model uninterpretable. Residualizing `size_mismatch` against `atomic_radius_mean` breaks this coupling, allowing the model to estimate the unique effect of size mismatch.

**Why Zenodo First?**
The Zenodo dataset is the only *verified* source for metallic glass CTE data in the available list. MP/AFLOW are supplementary and require API keys. Using Zenodo first ensures the pipeline is "CI-safe" and meets the "Verified Accuracy" constitution principle.

## References
- **Constitution**: `projects/PROJ-375-predicting-the-influence-of-composition-.yaml`
- **Spec**: `specs/001-gene-regulation/spec.md`
- **Dataset**: Zenodo - Metallic Glass Thermal Expansion Dataset (DOI: 10.5281/zenodo.1000000).
- **Spec Flags**: 
  - SC-003 (Circular Validation): Flagged for amendment. Stability Analysis used instead.
  - US-3 (Tautological Constraint): Flagged for amendment. Observed p-value reported.
  - FR-003 (Split Definition): Flagged for amendment. 3-way split used.
