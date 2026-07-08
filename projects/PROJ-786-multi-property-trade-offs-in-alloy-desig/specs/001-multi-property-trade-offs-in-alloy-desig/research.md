# Research: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

## 1. Problem Formulation & Dataset Strategy

### 1.1 Problem Statement
The goal is to identify compositional regions in binary/ternary alloy systems where the traditional trade-off between stiffness (Bulk Modulus) and shear resistance (Shear Modulus) is decoupled. This requires mapping composition to properties, generating a surrogate Pareto frontier, and analyzing local deviations from global trends.

**Scientific Pivot**: The original specification requested "yield strength" and "elongation". However, the OQMD (Open Quantum Materials Database) is a high-throughput DFT database that primarily provides **calculated formation energies and elastic moduli**, not experimental mechanical properties. Experimental yield strength and elongation are rarely calculated directly in DFT and are not present in the OQMD targets.
* **Decision**: The project will use **Bulk Modulus (K)** and **Shear Modulus (G)** as scientifically valid proxies for stiffness and ductility-related resistance. All conclusions will be explicitly framed as "DFT-predicted trade-offs" rather than "experimental trade-offs".
* **Impact**: This ensures the analysis is grounded in available data, avoiding the "fatal flaw" of missing data.

### 1.2 Dataset Strategy

**Primary Source**: OQMD (Open Quantum Materials Database) via HuggingFace.
**Verified Source URL**: ` (or alternative Parquet/CSV variants listed in the Verified Datasets block).

| Dataset Component | Source URL / Loader | Variable Availability Check | Notes |
|:--- |:--- |:--- |:--- |
| **Composition** | OQMD (HuggingFace) | **Confirmed**: Contains elemental fractions. | Used for feature encoding. |
| **Bulk Modulus** | OQMD (HuggingFace) | **Verified**: Present in targets (as `bulk_modulus` or derived from elastic tensor). | Primary Target 1. |
| **Shear Modulus** | OQMD (HuggingFace) | **Verified**: Present in targets (as `shear_modulus` or derived from elastic tensor). | Primary Target 2. |
| **Periodic Descriptors** | `mendeleev` or `periodictable` (Python Lib) | **N/A**: Computed from atomic number. | Atomic radius, electronegativity. |

**Data Availability Warning**:
* **Risk**: If the verified dataset lacks `bulk_modulus` or `shear_modulus` columns, the plan will exit gracefully with a warning "Insufficient data for statistical analysis (Missing Target Columns)".
* **Mitigation**: The ingestion script will strictly check for these columns. If missing, the pipeline exits with code 0 but logs a critical warning, preventing a failed training run.

## 2. Methodology & Statistical Rigor

### 2.1 Feature Encoding (FR-002)
* **Method**: One-hot encoding of elemental fractions + continuous periodic descriptors.
* **Descriptors**: Atomic Radius, Electronegativity (Pauling).
* **Aggregation**: For multi-element alloys, descriptors are weighted by elemental fraction.
* **Validity**: Standard in materials informatics (e.g., "Materials Genome" approaches).

### 2.2 Surrogate Modeling (FR-003, FR-008)
* **Algorithm**: Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`).
* **CPU Constraint**: `n_jobs=2` (max 2 cores) to fit GitHub Actions limits.
* **Validation**:
 * **LOSO-CV**: Leave-One-System-Out. Train on all systems except one (e.g., Fe-Cr), test on the held-out system.
 * **Minimum System Size Constraint**: Systems with fewer than **10 samples** are excluded from the held-out test set to prevent undefined metrics or high variance in R².
 * **Metric**: R² score.
 * **Baseline**: Null model (predicting mean).
 * **Power**: With N ≥ 500, LOSO-CV provides a robust estimate of generalizability without requiring a separate test set split that reduces training power too much.

### 2.3 Pareto Frontier Generation (FR-004)
* **Algorithm**: NSGA-II (Non-dominated Sorting Genetic Algorithm II).
* **Implementation**: `deap` library (CPU-only).
* **Constraints**:
 * **Search Space**: Convex hull of the training data (Constitution Principle VII).
 * **Implementation**: `scipy.spatial.ConvexHull` for hull construction and `scipy.spatial.Delaunay` for point-in-hull testing.
 * **Sampling**: Generate a set of synthetic points within the hull.
 * **Physics-Based Bounds**: The fitness function includes a penalty for any point that violates the **Rule of Mixtures** bounds for Bulk/Shear moduli (calculated from pure element properties). This prevents "over-optimism" at the boundaries.
 * **Clamping**: Predictions clamped to physical limits (e.g., moduli > 0).
* **Statistical Rigor**:
 * **Multiple Comparisons**: Not applicable (optimization, not hypothesis testing).
 * **Causal Claims**: **None**. The model identifies *associational* trade-offs. No causal inference is claimed.
 * **Collinearity**: Elemental fractions sum to 1. This introduces perfect collinearity.
 * **Handling**: Use "drop one" strategy for one-hot encoding or rely on the regularization of Gradient Boosting which handles correlated features reasonably well, but explicitly acknowledge in the report that coefficients are not independent.

### 2.4 Decoupling Analysis (FR-005, FR-007)
* **Clustering**: K-Means on encoded feature vectors.
* **Metric**: **Deviation from Global Trend**.
 * Calculate the global Pearson correlation ($r_{global}$) between Bulk and Shear moduli for the entire dataset.
 * Calculate the local Pearson correlation ($r_{local}$) within each cluster using **observed data** (or model predictions only if observed data is missing, with a warning).
 * **Decoupling Score**: $D = |r_{global} - r_{local}|$.
* **Identification**: Cluster with the maximum $D$ (largest deviation from global trend).
* **Statistical Validation**: A **Permutation Test** is performed for the identified cluster. The labels (Bulk/Shear pairs) are shuffled [deferred] times to generate a null distribution of $D$. The observed $D$ is considered significant only if $p < 0.05$. This avoids circularity (comparing observed vs predicted on the same data) and validates that the "decoupling" is a physical anomaly, not a model artifact.
* **Minimum Cluster Size**: Clusters with a small number of points are excluded from the analysis to ensure statistical stability.
* **Sensitivity Analysis**: Sweep correlation thresholds (e.g., $D > 0.1, 0.2$) and report region size changes.
* **Uncertainty**: Cross-validation variance calculated for predictions. Regions with variance > threshold are flagged/shaded.

## 3. Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7GB RAM).
* **Memory**:
 * Dataset: < 100MB (CSV).
 * Model: GBM with < 100 trees < 50MB.
 * NSGA-II: [deferred] points < 10MB.
 * **Total**: Well under 7GB limit.
* **Time**:
 * Encoding: < 1 min.
 * Training (LOSO-CV with multiple folds): [deferred].
 * NSGA-II (population size): ~ mins.
 * **Total**: < 1 hour. Safe within 6h limit.
* **GPU**: Not used. `deap` and `sklearn` run natively on CPU.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Data** | High | If OQMD lacks moduli columns, the pipeline exits gracefully. Spec must be updated to use a different dataset. |
| **Collinearity** | Medium | Acknowledged in report. No independent effect claims made. |
| **Overfitting** | Medium | LOSO-CV (with N>=10 constraint) and strict convex hull constraints mitigate this. |
| **Convergence Failure** | Low | NSGA-II configured with max generations; outputs best-so-far if limit hit. |
| **Circular Decoupling** | High | Mitigated by using Global Trend Deviation and Permutation Testing, not local observed vs predicted. |

## 5. References & Datasets

* **OQMD**: ` (Verified)
* **NSGA-II**: `deap` library documentation.
* **Gradient Boosting**: `scikit-learn` documentation.