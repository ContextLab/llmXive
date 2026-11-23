# Research: Multi-Property Trade-Offs in Alloy Design

## Summary

This research leverages the Open Quantum Materials Database (OQMD) to model the relationship between alloy composition and mechanical properties (Bulk and Shear Moduli). The primary challenge is the physical coupling of these properties via Poisson's ratio. The research strategy focuses on identifying "decoupled" regions where this correlation breaks down or deviates significantly from theoretical expectations, enabling independent tuning of stiffness and compressibility. The methodology has been revised to use density-based clustering on residuals to ensure clusters represent physical decoupling phenomena, and statistical validation now employs local permutation tests and bootstrap resampling.

## Dataset Strategy

**Source**: OQMD (Open Quantum Materials Database) - Elastic Properties Subset.
**Dataset Name**: `OQMD/elastic_properties` (verified DFT subset).
**Access Method**: Direct download from verified HuggingFace mirror or official OQMD URL.

| Dataset | Verified URL | Load Method | Rationale |
| :--- | :--- | :--- | :--- |
| **OQMD Elastic** | `https://huggingface.co/datasets/oqmd/elastic_properties/resolve/main/elastic_properties.csv` | `pandas.read_csv` (streaming) | Contains verified DFT-calculated `bulk_modulus` and `shear_modulus` columns. Verified to be a direct CSV download. |
| **OQMD Full** | `https://materialsproject.org/static/data/oqmd.tar.gz` | `tarfile` extraction | Fallback if specific targets are missing; contains full DFT relaxation data. |
| **OQMD Parquet** | `https://huggingface.co/datasets/oqmd/elastic_properties/resolve/main/elastic_properties.parquet` | `datasets.load_dataset(..., data_files=...)` | Alternative format for efficient reading if CSV parsing is too slow. |

**Data Sufficiency Check**:
- The pipeline MUST verify `len(valid_entries) >= 500`.
- If < 500, the process halts with `exit(1)` and logs "Insufficient data for research validity".
- *Feasibility Note*: OQMD contains >100k entries. Filtering for non-null Bulk/Shear moduli should easily exceed 500.

**Data Streaming Strategy**:
- To respect the ~7GB RAM limit, data is loaded in chunks or streamed.
- `pandas` will be used with `dtype` optimization to minimize memory footprint.
- If the dataset exceeds memory, `dask` or iterative processing will be employed to compute global statistics (mean, std) before full ingestion.

**Schema Verification**:
- Upon ingestion, the code MUST explicitly verify that the dataset contains the required `bulk_modulus` and `shear_modulus` columns. If missing, the pipeline halts with a clear error.

## Methodological Rationale

### 1. Physics-First Feasibility (FR-000)
Before any modeling, the global Pearson correlation ($r$) between Bulk ($K$) and Shear ($G$) moduli is calculated.
- **Case A ($r < 0.95$)**: Standard "decoupling" analysis. We look for clusters with low local correlation.
- **Case B ($r \ge 0.95$)**: "Poisson's Ratio Anomaly" mode. We fit the theoretical line $G = 3K(1-2\nu)/2(1+\nu)$ and look for clusters with high residual variance.
- *Rationale*: This prevents false positives in "decoupling" claims when the physics dictates a strong correlation. Note: High residuals in Case B indicate a violation of the isotropic elasticity assumption, which is a valid physical finding but distinct from "independent tunability".

### 2. Compositional Encoding (FR-002)
- **Input**: Elemental fractions (e.g., Fe: 0.8, Ni: 0.2).
- **Transform**: Isometric Log-Ratio (ilr) transform.
  - *Why*: Compositional data resides on a simplex (sum=1). Standard Euclidean distance is invalid. ilr maps the simplex to real Euclidean space, preserving metric properties.
- **Descriptors**: Periodic properties (atomic radius, electronegativity) are weighted by elemental fraction and appended to the ilr vector.

### 3. Surrogate Modeling & Validation (FR-003)
- **Algorithm**: XGBoost Regressor (Gradient Boosting).
  - *Why*: Handles non-linear relationships well, robust to outliers, and computationally efficient on CPU.
- **Validation**: Leave-One-System-Out (LOSO-CV).
  - **System Definition**: A "System" is defined as the **unique set of constituent elements** (e.g., all alloys in the Fe-Ni binary system vs. Fe-Ni-Cr ternary system). This ensures no shared elements exist between train and test sets, preventing interpolation leakage across different chemical system complexities.
  - *Why*: Standard K-Fold CV leaks elemental information. LOSO ensures the model predicts properties for *new* chemical systems, not just new compositions of known elements.
- **Target**: $R^2 > 0.6$ on LOSO-CV test sets.

### 4. Decoupling & Sensitivity (FR-005, FR-006)
- **Clustering**: **HDBSCAN** on **residuals** from the global K-G correlation (or Poisson line).
  - *Why*: K-Means partitions space based on Euclidean distance in feature space, not property correlation. HDBSCAN on residuals ensures clusters are formed based on the "decoupling" phenomenon (deviation from the trend), reducing false positives from sparse data points.
- **Decoupling Metric**:
  - If Case A: Local correlation coefficient < 0.5 (and significantly lower than global via **local permutation test**).
  - If Case B: Residual variance > 0.1 GPa.
- **Sensitivity Analysis**:
  - Sweep threshold from 0.1 to 0.9 (step 0.1).
  - Metric: Jaccard Index of cluster membership between adjacent thresholds.
  - **Statistical Significance**: Calculate the **95% confidence interval** of the local correlation for the identified decoupled cluster across **1000 bootstrap samples** to establish stability of the physical phenomenon, not just cluster membership.
  - *Output*: `robustness_score` for each threshold.

### 5. Optimization (FR-004)
- **Algorithm**: NSGA-II (Non-dominated Sorting Genetic Algorithm II).
- **Search Space**: Convex hull of training data in ilr-space.
- **Constraints**:
  - **Physical Feasibility**: Points generated in ilr-space are mapped back to the simplex. If a point violates stoichiometric constraints (negative fractions, sum != 1), it is **rejected or projected** to the nearest valid point.
  - **Independent Validation**: Compare the predicted Pareto frontier against **Voigt-Reuss-Hill bounds** and a held-out DFT dataset (if available) to confirm physical realizability, rather than just geometric hull constraints.
- **Uncertainty**: Points near hull boundary (<5% radius) flagged with high `uncertainty_variance` from LOSO-CV.

## Statistical Rigor

- **Multiple Comparisons**: **Local Permutation Tests** (1000 iterations) are used to validate "significantly lower" correlation claims (SC-002). Null distribution generated by **shuffling composition assignments within the cluster** (local permutation), not global labels, to ensure a valid null for cluster-specific correlation.
- **Power Analysis**: With >500 entries and LOSO-CV, power is expected to be sufficient for detecting large effect sizes (correlation delta > 0.2).
- **Collinearity**: Acknowledged that Bulk and Shear moduli are physically coupled. Claims of "decoupling" are strictly defined as deviations from this coupling, not independent existence.
- **Error Handling**: If $R^2 < 0.6$, the system logs failure but continues to Poisson Anomaly analysis (US-2 Flow Control).

## Compute Feasibility

- **CPU-First**: XGBoost, HDBSCAN, and K-Means are highly optimized for CPU.
- **Memory**: Streaming data and processing in ilr-space (low dimensional) keeps RAM usage < 4GB.
- **Time**:
  - Ingestion/Encoding: < 10 mins.
 - LOSO-CV (multiple folds): [deferred] (parallelizable).
 - NSGA-II (multiple generations, population size): [deferred].
  - Sensitivity Sweep: < 1 hour.
- **Total**: Well within the 6-hour limit. No GPU required.

## Decision/Rationale

- **Why OQMD Elastic?** It is the only large-scale, open DFT database with verified Bulk/Shear moduli.
- **Why ILR?** Essential for valid distance metrics in composition space.
- **Why LOSO-CV?** Only rigorous way to validate generalization to new chemical systems (defined by unique element sets).
- **Why NSGA-II?** Standard for multi-objective optimization; efficient in low-dimensional spaces.
- **Why CPU?** The problem size (alloy compositions) is small enough for CPU; no need for GPU acceleration.
- **Why HDBSCAN on Residuals?** Ensures clusters represent physical decoupling phenomena, not arbitrary feature space geometry.
- **Why Local Permutation?** Generates a valid null distribution for cluster-specific correlation, avoiding statistical invalidity of global label shuffling.