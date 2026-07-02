# Research: Quantify Dataset Sparsity Impact

## 1. Problem Statement & Research Question

**Question**: How does dataset sparsity (reduction in training set size) impact the predictive performance (RMSE, MAE) and uncertainty calibration of Machine Learning models for material stability *within a Representative Stratified Sample*?

**Hypothesis**: Performance degrades non-linearly as sparsity increases, with a distinct "elbow point" where additional data yields diminishing returns *within the 30k sample*. GPR models may show better uncertainty calibration than Random Forests at low sparsity levels.

**Scope Clarification**: The study explicitly measures sparsity impact on a **[deferred]-entry Representative Stratified Sample (RSS)** of the full Materials Project dataset. The "[deferred]" baseline is this 30k sample, not the full 150k. This avoids extrapolation claims and ensures computational feasibility on CPU-only free-tier runners. The 150k figure represents the **Source Pool** from which the RSS is drawn.

## 2. Dataset Strategy

### 2.1 Data Source Verification

The spec requires DFT-computed formation energy data from the Materials Project.

**Constraint Check**: The `# Verified datasets` block provided in the user message **does not contain a verified URL** for the Materials Project DFT-computed formation energy dataset.

**Action**:
1.  The implementation **MUST NOT** fabricate a URL for the Materials Project dataset.
2.  The pipeline will attempt to fetch data via the official `MaterialsProject` Python API (which requires an API key, typically provided via environment variable `MP_API_KEY`), as this is the standard programmatic access method.
3.  If the API is inaccessible or the key is missing, the pipeline will **fail gracefully** with a clear error message, rather than falling back to a non-verified source.
4.  For the purpose of this plan, we assume the user will provide a valid API key or a pre-downloaded CSV that matches the schema defined in `contracts/`.

**Spec Contradiction Note**: The spec's Assumptions state "Materials Project public API is available without authentication barriers". This is factually incorrect (requires `MP_API_KEY`). This assumption must be updated in the spec.

### 2.2 Data Characteristics & Variable Fit

*   **Target Variable**: `formation_energy_per_atom` (DFT-computed).
*   **Predictors**: Elemental composition descriptors (atomic number, electronegativity, atomic radius averages) generated via `matminer`.
* **Fit Check**: The spec assumes the dataset contains sufficient formation energy entries (>150k). If the API returns fewer entries, the plan will dynamically adjust the sparsity levels (e.g., if only 50k entries are available, the "[deferred]" level becomes 50k, and subsamples are scaled accordingly) to prevent errors, while logging a warning that the absolute scale is reduced.

**Verified Sources List (for citation)**:
*   Materials Project API (Programmatic access, no public static URL in verified list).
*   *Note: The provided verified list contains protein datasets (SAME) which are **not** relevant to this material stability study. These will **not** be cited.*

## 3. Methodology & Statistical Rigor

### 3.1 Sparsity Subsampling (FR-003)

To preserve chemical space, simple random sampling is insufficient.
*   **Method**: K-Means clustering on elemental fingerprints (composition vectors).
*   **Process**:
    1.  Compute fingerprints for all materials.
    2.  Cluster into $K$ clusters (where $K$ is large enough to capture chemical diversity, e.g., $K=1000$).
    3.  Stratified sampling: For a target sparsity $S\%$, sample $S\%$ of materials from *each* cluster.
*   **Rationale**: This ensures that rare elements and specific chemical families are represented proportionally in every subset, preventing bias where a sparse subset might lack a specific class of materials entirely.
* **Baseline Cap**: The "[deferred]" level is capped at **[deferred] entries** (Representative Stratified Sample) to ensure GPR feasibility. Lower levels are nested subsamples of this 30k pool.
* **Clarification**: The "[deferred]" point is a stratified sample of the full dataset, not the full set. The "sparsity" levels ([deferred], [deferred]...) are subsamples of this 30k cap. This means the "[deferred]" point is not the ground truth of the full dataset, but a specific realization of a stratified sample. The performance degradation curve measures the effect of reducing a *sample* of the data, not the effect of data sparsity on the *full* chemical space representation. The 'elbow' found is an artifact of the 30k cap, not a fundamental property of the dataset.

### 3.2 Stratification Validation (New)

Before training, the plan MUST verify that stratification preserved chemical space.
*   **Metrics**:
    *   **Jensen-Shannon Divergence**: On descriptor distributions between subset and 30k pool. Threshold: < 0.05.
    *   **Kolmogorov-Smirnov Test**: On formation energy distributions. Threshold: p-value > 0.05.
*   **Action**: If validation fails, the subset is regenerated with a new seed or the clustering parameters are adjusted.

### 3.3 Model Training (FR-004, FR-005)

*   **Models**:
    1.  **Gaussian Process Regression (GPR)**: RBF Kernel.
        *   *Constraint*: Full GPR is $O(N^3)$.
 * *Adaptation*: Use `sklearn.gaussian_process.GaussianProcessRegressor` with `normalize_y=True`. The input data is capped at 30k samples. This configuration is known to fit within 7GB RAM on 2 CPU cores for $N \le [deferred]$.
    2.  **Random Forest (RF)**: Ensemble of decision trees.
 * *Constraint*: $O(N \log N)$ per tree. Feasible for $N \approx [deferred]$ on 2 CPU cores if `n_estimators` is limited (e.g., 100).
*   **Cross-Validation**: 5-fold CV, 3 seeds per sparsity level.
*   **Metrics**: RMSE, MAE, **Predictive Variance** (for GPR uncertainty calibration).

### 3.4 Fixed Test Set (FR-009)

* **Strategy**: A fixed test set ([deferred] of the full 150k pool) is partitioned **immediately after ingestion**, *before* any sparsity generation.
* **Usage**: All models (from [deferred] to [deferred] training levels) are evaluated on this **same** fixed test set.
*   **Rationale**: This prevents circular dependency and ensures that performance differences are due to training set size, not test set variance. The test set is independent of the 30k RSS training baseline.

### 3.5 Statistical Analysis (FR-006, FR-007, FR-010)

*   **Design**: **Linear Mixed-Effects Model (LMM)**.
 * *Why*: The sparsity levels are nested ([deferred] is a subset of [deferred], etc., all within the 30k pool). Standard ANOVA assumes independence, which is violated. Repeated Measures ANOVA assumes the same subjects across conditions, which is also violated here (different data points in each subset).
    *   *Model*: `Performance ~ Sparsity_Level + (1 | Subset_ID)`.
    *   *Correction*: Tukey HSD post-hoc test for pairwise comparisons on fixed effects.
*   **Sensitivity Analysis (FR-007)**:
    *   Calculate the slope of the learning curve between adjacent sparsity levels.
 * Verify that the slope variance between adjacent levels (e.g., [deferred] vs [deferred]) is < 10%.
    *   Identify the "elbow point" where the slope stabilizes.
*   **Causal Claims**: The study is **observational** (we are subsampling existing data). We **cannot** claim that "adding data causes performance to improve" in a causal sense for new materials. Claims will be framed as **associational**: "Higher data density is associated with lower error rates *within the representative sample*."
*   **Collinearity**: Elemental descriptors (e.g., atomic radius vs. atomic number) are often correlated. The plan will calculate Variance Inflation Factors (VIF) and, if high, report the model performance as a composite effect rather than claiming independent effects for specific descriptors.

### 3.6 Uncertainty Calibration (Constitution VI)

*   **Method**: For GPR models, compare predicted variance to squared residuals on the fixed test set.
*   **Output**: Calibration slope and a plot of `Predicted Variance` vs `Squared Residual`.
*   **Storage**: Stored in `data/results/calibration/`.

### 3.7 Compute Feasibility & Risk Mitigation

*   **Risk**: GPR training on >30k samples crashes on 7GB RAM.
*   **Mitigation**:
 1. **Hard Cap**: The "[deferred]" level is strictly capped at [deferred] samples.
    2.  **Sequential Processing**: Process folds sequentially, not in parallel, to keep peak memory low.
    3.  **Chunking**: If memory error occurs, further reduce `n_estimators` in RF or use a smaller subset for GPR.

## 4. Ethical & Reproducibility Considerations

*   **Reproducibility**: All seeds pinned. Code versioned.
*   **Bias**: Stratified sampling minimizes selection bias. Validation step ensures this.
*   **Transparency**: Calibration reports for GPR will be published. Metadata for every subset is stored.

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use K-Means for Stratification** | Preserves chemical diversity better than simple random sampling. |
| **Cap "[deferred]" level at [deferred] samples** | Ensures GPR training fits within 7GB RAM on CPU. Full 150k is infeasible for GPR without heavy approximations that may degrade accuracy. |
| **Linear Mixed-Effects Model (LMM)** | Correctly handles the nested structure of sparsity subsets ([deferred] within 10% within 30k) where ANOVA assumptions fail. |
| **Associational Framing** | Spec requires avoiding causal claims; observational subsampling cannot prove causality. |
| **Fixed Test Set** | Prevents circular dependency and ensures consistent evaluation across all levels. |
| **No External Dataset URL** | Verified list lacks MP URL; using API or local file as per spec. |
| **Stratification Validation** | Ensures that performance degradation is due to data volume, not chemical bias introduced by sampling. |


## 6. Sparsity Levels

The 7 levels are defined as percentages of the **[deferred] Representative Stratified Sample**:
1. A subset of samples, representing approximately 5% of the total dataset, will be selected for analysis.
2. (a substantial set of samples)
3. (a representative subset of samples)
4. (a large sample)
5. (a substantial sample size)
6. A substantial portion (approximately 80% of the total sample)
7. A comprehensive dataset of a large-scale sample size will be utilized.