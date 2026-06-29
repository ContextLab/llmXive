# Research: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Dataset Strategy

The primary dataset is **Materials Project MP-2020.12.1**.
- **Source**: Zenodo Record **10.5281/zenodo.4053859**.
- **Verified Status**: **Verified**. This DOI points to a stable, accessible snapshot of the MP-2020.12.1 dataset.
- **Action Plan**:
  1. The `ingest.py` script will download from the verified Zenodo URL.
  2. A checksum verification step will ensure data integrity against the recorded hash.
  3. **Dataset Variable Fit**: The dataset contains `formation_energy_per_atom`, `composition` (chemical formula), and `crystal_system`. The plan will compute `chemical_family` (most abundant element) for stratification.

## Methodological Rationale

### 1. Feature Engineering (FR-002)
- **Descriptors**: Mean and Variance of:
  - Electronegativity (Pauling)
  - Atomic Radius
  - Valence Electrons
  - Melting Point
  - First Ionization Energy
- **Justification**: These are standard compositional descriptors in materials informatics.
- **Handling Missing Data**: If an element lacks a property, the row will be excluded. The count of excluded rows will be logged.

### 2. Model Selection (FR-003)
- **Random Forest (RF)**: `n_estimators=200`, `max_depth=20`.
  - *Rationale*: Robust to non-linearities; provides built-in feature importance.
  - *CPU Feasibility*: 200 trees on 50k samples is tractable on 2 CPU cores within 3 hours.
- **Gradient Boosting (GB)**: `n_estimators=100`.
  - *Rationale*: Higher accuracy potential; included for comparison.

### 3. Validation Strategy (FR-004)
- **Split**: 80/20 Stratified by **Chemical Family** (most abundant element).
  - *Why*: Crystal system is a structural property and does not guarantee compositional generalization. Stratifying by Chemical Family ensures the model is tested on chemical classes it hasn't seen, preventing bias towards dominant chemistries. This supersedes the legacy spec assumption of 'crystal system' stratification.
- **Metrics**: R², MAE, RMSE.
- **Overfitting Check**: Compare Train vs. Validation R². If `Train_R² - Val_R² > 0.1`, flag as overfitting.

### 4. Multicollinearity Check (VIF) & Feature Importance (FR-005, FR-006)
- **VIF Analysis**: Before ranking, compute Variance Inflation Factor (VIF) for all descriptors.
  - If VIF > 5 for a feature pair (e.g., Mean and Variance of Electronegativity), the plan will either:
    1. Drop the variance feature (retaining the mean), or
    2. Group them and report the 'Property' importance rather than individual feature importance.
- **Tree-based Importance**: From RF `feature_importances_`.
- **Permutation Importance**: To validate stability (SC-002).
- **Partial Dependence Plots (PDP)**: Visualize marginal effects of top 3 features (SC-003).

### 5. Null Model Baseline
- **Purpose**: To prove the model is not just memorizing trivial periodic trends.
- **Method**: Train a model where elemental properties are shuffled (permuted) across elements.
- **Validation**: The main model's R² must be significantly higher than the Null Model's R². If not, the correlation is deemed trivial.

## Statistical Rigor & Limitations

- **Power Analysis**: For 10 predictors and alpha=0.05, a sample size of 50,000 (the capped size) provides >99% power to detect a small effect size (f²=0.02). This confirms the statistical validity of the regression.
- **Multiple Comparisons**: Not applicable for the main regression. Paired t-tests will be used for model comparison.
- **Causal Claims**: None. The study is observational (correlational). Claims will be framed as "associations" or "predictive power."
- **Measurement Validity**: Elemental properties are taken from `pymatgen`'s built-in database (standard reference).

## Compute Feasibility Check

- **Memory**: The raw dataset is approximately 2 GB. Processing in chunks and capping at [deferred] rows will keep RAM usage < 4 GB.
- **Time**: RF (200 trees) on 50k rows [deferred] on 2 cores. GB [deferred]. Total pipeline < 6 hours.
- **GPU**: Not used.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Zenodo Mirror Unreachable** | Script exits with error; project blocked until source is verified. No fallback URL invented. |
| **Dataset Missing Columns** | Script validates schema on load; fails fast if `formation_energy_per_atom` or `composition` is missing. |
| **RAM Exceeded** | Script monitors memory; if > 6 GB, it automatically samples to 50k rows (stratified by Chemical Family) and logs the reduction. |
| **Overfitting** | If Train/Val gap is large, the plan will report the discrepancy and not claim high predictive power. |
| **Multicollinearity** | VIF analysis will detect and handle correlated features before ranking. |
