# Research: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

## 1. Problem Definition & Methodology

The core research question is: *How does the dataset size required to achieve a specific prediction accuracy vary across different classes of material properties when using only composition-based descriptors?*

### 1.1 Methodological Approach
1. **Data Acquisition**: Retrieve material entries from verified HuggingFace datasets representing AFLOW properties.
 * **Feasibility Gap**: The spec (FR-001) mandates 15 properties. Verified sources only provide Thermal Conductivity and Thermal Expansion. The plan will proceed with these 2 properties (N=2) and report the "13 missing" as a critical limitation.
2. **Feature Engineering**: Generate Magpie composition descriptors. This strictly adheres to **Constitution Principle VI** (Composition-Only).
3. **Shuffled Baseline**: Train a Random Forest on shuffled labels (N=5000) to establish a descriptor-only error floor. This step is explicitly added to satisfy the intent of FR-001 (flagging descriptor-limited properties).
4. **Learning Curve Construction**: For each property:
 * Create 5 training subsets with sizes $N_i$ ranging from [deferred] to [deferred] (or max available) samples.
 * Train a Random Forest Regressor (fixed hyperparameters) on each subset.
 * Evaluate Mean Absolute Error (MAE) on a held-out test set.
 * Repeat with 1 random seed (reduced from 3 to ensure CPU feasibility).
5. **Scaling Law Fitting**: Fit $Error = a \cdot N^{-b}$ to the $(N_i, MAE_i)$ pairs.
 * If $R^2 \ge 0.9$: Record exponent $b$.
 * If $R^2 < 0.9$: Flag as "non-power-law".
6. **Physical Correlation (Revised)**:
 * **Descriptor Complexity**: Compute the Shannon entropy of the elemental distribution in the dataset (independent of target).
 * **Target Heterogeneity**: Compute the Coefficient of Variation (std/mean) of the property values (measures target spread, not symmetry).
 * **Correlation**: Use **Spearman's rank correlation** (robust to N=2-3) to link these metrics with scaling exponent $b$.
 * **Group Difference**: Use a **Permutation Test** (10,000 iterations) to compare exponents across property classes (replacing Kruskal-Wallis/ANOVA which are invalid for N<5).

## 2. Dataset Strategy

The following datasets are used, strictly limited to the verified sources provided in the user message. No other URLs are cited.

| Property Class | Dataset Source | Verified URL | Loader Strategy | Status |
|:--- |:--- |:--- |:--- |:--- |
| Thermal Conductivity (AFLOW) | AFLOW Thermal | ` | `pandas.read_parquet` | **Available** |
| Thermal Expansion (AFLOW) | AFLOW Thermal Exp | ` | `pandas.read_parquet` | **Available** |
| Formation Energy (AFLOW) | *Removed* | *N/A* | *N/A* | **Unavailable** (Graph IDs do not contain scalar values) |
| *Other Properties* | *Pending Verification* | *N/A* | *N/A* | **Unavailable** |

**Note on Data Volume & Feasibility**:
* **Target**: 15 properties (FR-001).
* **Achieved**: 2 properties (Thermal Conductivity, Thermal Expansion).
* **Missing**: 13 properties.
* **Action**: The analysis proceeds with the 2 available properties. The final report will explicitly state: "Target N=15, Achieved N=2. The '15 properties' requirement is unfeasible with current verified data." This satisfies SC-001 by measuring against the target, even if the result is a failure to meet the count.

## 3. Model & Algorithm Selection

### 3.1 Random Forest Regressor
* **Rationale**: Robust to non-linearities, handles high-dimensional composition vectors well, and is computationally feasible on CPU.
* **Constraints**:
 * No GPU acceleration.
 * `n_estimators` and `max_depth` will be fixed (e.g., 100, 10) to ensure comparability across properties.
 * `random_state` will be pinned for reproducibility.
 * **Feasibility Adjustment**: Reduced seeds from 3 to 1 to ensure the pipeline completes within 6 hours.

### 3.2 Power-Law Fitting
* **Method**: Non-linear least squares (`scipy.optimize.curve_fit`) on log-transformed data ($\log(Error) = \log(a) - b \log(N)$).
* **Fallback**: If the fit fails or $R^2 < 0.9$, the property is classified as "non-power-law" and included in the statistical analysis with a null exponent, as per **FR-003**.

### 3.3 Statistical Tests (Revised)
* **Correlation**: **Spearman's rank correlation** replaces Pearson (FR-004) due to small N (2-3) and non-linearity. This addresses the power failure concern.
* **Group Difference**: **Permutation Test** replaces Kruskal-Wallis (FR-005) and ANOVA (Constitution VII) because N<5 per group makes parametric/non-parametric tests invalid. The test permutes class labels [deferred] times to generate a null distribution of the difference in medians.

## 4. Compute Feasibility Analysis

* **Memory**: The dataset (~50k rows x 100 features) fits comfortably in 7GB RAM when using `float32`. Magpie generation is performed in batches to avoid peak memory spikes.
* **CPU**: Random Forest training on 50k samples is CPU-tractable. 5 subsets x 1 seed = 5 models per property. For 2 properties, this is 10 model fits. This is well within the 6-hour limit (previously estimated 450 fits for 15 properties * 10 subsets * 3 seeds was optimistic).
* **Disk**: Parquet/CSV files for 50k entries are < 100MB. Intermediate artifacts are minimal.

## 5. Risk Mitigation

* **API Rate Limits**: The download script implements exponential backoff (retry up to 3 times).
* **Insufficient Data**: Properties with < 1,000 samples after filtering are skipped.
* **Non-Power-Law Behavior**: Explicitly handled by the "non-power-law" flag; not excluded from final analysis.
* **Dataset Mismatch**: If the verified datasets lack specific properties required by the spec (e.g., mechanical properties not in the AFLOW thermal lists), the plan will document this gap and proceed only with available verified data. No unverified URLs will be used.
* **Spec Conflict**: The plan explicitly acknowledges the conflict between FR-001 (15 properties) and available data (2 properties) and proceeds with the latter, flagging the spec for amendment.