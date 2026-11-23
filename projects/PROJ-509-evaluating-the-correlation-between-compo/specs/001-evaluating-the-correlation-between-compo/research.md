# Research: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Problem Statement & Context

The formation energy of inorganic materials is a critical property for predicting stability and synthesizability. While deep learning models (e.g., MEGNet, CGCNN) exist, this study focuses on the interpretability of simple compositional descriptors. The research question is: *To what extent do mean and variance of elemental properties (electronegativity, atomic radius, valence electrons, melting point, ionization energy) correlate with and predict formation energy?*

This study addresses the "black box" nature of complex models by using tree-based regressors (Random Forest, Gradient Boosting) which provide explicit feature importance metrics. The analysis is restricted to inorganic compounds to ensure chemical homogeneity.

## Dataset Strategy

The primary dataset is the **Materials Project MP-2020.12.1** verified subset.

| Dataset Name | Source/URL | Access Method | Notes |
| :--- | :--- | :--- | :--- |
| **MP-2020** | Materials Project (via MPDS API) | Programmatic download via `matminer` `MPDS` loader. Requires `MPDS_API_KEY` in CI secrets. | Contains a substantial collection of inorganic compounds. Requires filtering for complete composition and formation energy. |
| **Q47604** | https://www.wikidata.org/wiki/Q47604 | Reference only | Used as a reference for dataset existence and scale (a substantial number of rows verified), but NOT a direct download source. |

**Data Availability & Feasibility Assessment**:
- **Primary Source**: The MP-2020 dataset is the standard for this domain. Access is via the Materials Project Data Service (MPDS) API, which requires an API key. The pipeline will attempt to fetch data using `matminer`'s `MPDS` loader with the `MPDS_API_KEY` environment variable.
- **Fallback Strategy**: Per FR-001, if the API fails (e.g., key missing, network error), the system will load from a pre-downloaded `data/raw/mp-2020.csv` file. This file MUST be checksummed (SHA-256) and versioned to satisfy Constitution Principle III (Data Hygiene) and Principle I (Reproducibility). If the checksum does not match the expected value, the pipeline will fail.
- **Streaming**: The dataset is small enough to load entirely into memory (a 7 GB RAM limit is safe for this size).
- **Variable Fit Verification**:
  - **Required Variables**: Formation Energy (`formation_energy_per_atom`), Chemical Formula (`pretty_formula`), Crystal System (`crystal_system`), Elemental Composition (stoichiometry).
  - **Derived Variables**: Mean/Var of Electronegativity, Atomic Radius, Valence, Melting Point, Ionization Energy.
  - **Fit**: The MP-2020 dataset contains the necessary elemental properties via `pymatgen`'s built-in element data. No external lookup is needed for standard elements. Rare elements with missing properties will be excluded (Edge Case handling).

## Methodology & Statistical Rigor

### 1. Data Preprocessing
- **Filtering**: Select only inorganic compounds (exclude organics based on carbon content or explicit `is_inorganic` flag if available).
- **Missing Data**: Exclude rows with missing formation energy or incomplete composition. Exclude rows where elemental properties (e.g., electronegativity) are missing for any constituent element.
- **Outlier Handling**: Cap formation energy values at the 1st and 99th percentiles to reduce skew (Edge Case).
- **Normalization**: No standardization required for tree-based models, but mean/variance descriptors will be computed directly.

### 2. Feature Engineering
- **Descriptors**: For each compound, compute:
  - Mean Electronegativity
  - Variance Electronegativity
  - Mean/Var Atomic Radius
  - Mean/Var Valence Electrons
  - Mean/Var Melting Point
  - Mean/Var First Ionization Energy
- **Chemical Family**: Derived via `code/utils/chemical_families.py` using the dominant element's group/block to assign a fixed set of families (e.g., Alkali, Transition, Oxide). This ensures consistent stratification.
- **Source**: `pymatgen`'s `Element` class for property lookup.

### 3. Model Training
- **Algorithms**: Random Forest (max_depth=20, n_estimators=200), Gradient Boosting (n_estimators=100).
- **Split**: 80/20 stratified split by **Chemical Family** (not crystal system) to control for compositional bias (Assumption).
- **Hardware**: CPU-only. `scikit-learn` is optimized for multi-core CPU.
- **Feasibility**: A moderate number of samples with multiple features is trivial for RF/GB on 2 CPU cores. Estimated time < 1 hour.

### 4. Evaluation & Validation
- **Metrics**: R², MAE, RMSE. Negative R² allowed (FR-004b).
- **Feature Importance**:
  - Tree-based importance (Gini/impurity).
  - **Conditional Permutation Importance**: Used instead of standard permutation to handle multicollinearity (concern methodology-ca621c6f).
  - **SHAP Interaction Values**: Computed to disentangle correlated feature effects and assess joint contributions.
  - **Collinearity**: VIF (Variance Inflation Factor) calculated. If VIF > 10, log warning but do NOT remove features (Edge Case, Assumption).
  - **Significance**: Permutation-based significance test (sufficient shuffles) to generate null distributions for importance scores, avoiding invalid t-tests on correlated estimates.
- **Sensitivity**: Accumulated Local Effects (ALE) plots for top 3 features (FR-006).
- **Non-linearity Score**: Defined as `|R²_quad - R²_lin|` (absolute difference in R² between a quadratic and linear fit to the ALE curve). A score > 0.5 indicates significant non-linearity (SC-003).
- **Power Analysis**: Minimum Detectable Effect Size (MDES) for Cohen's f² will be calculated post-hoc using the observed variance and sample size (N=12,500) at alpha=0.05. Current plan assumes sufficiency for medium effects (f² ≥ 0.15) but marks this as a [deferred] empirical check.

### 5. Multiple Comparison Correction & Model Comparison
- **Model Comparison**: Paired t-tests will be conducted comparing RF vs. GB validation scores on the same folds.
- **Correction**: If multiple metrics (R², MAE, RMSE) are tested, the Benjamini-Hochberg procedure will be applied to control FDR.
- **Output**: p-values and confidence intervals saved to `data/evaluation/statistical_tests.json`.

## Compute Feasibility

- **CPU-First**: All methods (RF, GB, ALE, Permutation, SHAP) are implemented in `scikit-learn`, `eli5`, and `shap` which run efficiently on CPU.
- **Memory**: A dataset of approximately ten thousand rows × a moderate number of features × float64 ≈ 1 MB. Even with overhead, < 100 MB RAM. Well within 7 GB limit.
- **Time**: Training RF (a moderate number of trees) on a large sample of data takes a short duration. ALE plots and SHAP take < 10 minutes. Total pipeline < 1 hour.
- **GPU Escape Hatch**: Not required. No deep learning models are used.

## Risk Assessment

- **Data Access**: If the MP-2020 dataset cannot be downloaded programmatically and no local cache exists, the pipeline fails. Mitigation: Ensure a checksummed CSV is committed to `data/raw/` as a fallback (Constitution III).
- **Overfitting**: If training R² >> validation R², the pipeline flags this and may skip feature importance analysis (Edge Case).
- **Collinearity**: High VIF is expected due to physical correlations. The plan explicitly handles this by logging warnings and using Conditional Permutation/SHAP rather than removing features (Edge Case).
- **Interpretation**: Mean and Variance descriptors are mathematically coupled. Rankings are interpreted as "predictive contribution" rather than "independent physical causation". SHAP interactions will be used to assess joint effects.
