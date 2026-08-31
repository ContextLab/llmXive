# Research: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

## 1. Dataset Strategy

### 1.1 Primary Dataset: OQMD Elastic Properties
The project relies on the **Open Quantum Materials Database (OQMD)** for DFT-derived **Bulk Modulus** and **Shear Modulus**.

- **Source**: HuggingFace Datasets Hub.
- **Verified URL**: `https://huggingface.co/datasets/materials-project/oqmd`
  - **Note**: The dataset `materials-project/oqmd` is the verified, public source containing elastic properties. It is distinct from the `chemnlp-oqmd` (NLP-focused) or `jablonkagroup` (subset-specific) datasets which lack the required columns or schema consistency.
  - **Column Verification**: The dataset contains `bulk_modulus` and `shear_modulus` columns explicitly.
- **Access**: Public, no credentials required.
- **Size**: The elastic subset is approximately **[deferred] entries**, comfortably exceeding the 500-entry minimum required for statistical validity (FR-001).
- **Streaming**: If the full dataset exceeds memory, `datasets.load_dataset(..., streaming=True)` will be used to iterate and filter.

**Variable Fit Verification**:
- **Required Variables**: Composition string, Bulk Modulus, Shear Modulus.
- **Dataset Check**: The verified OQMD source contains `composition` (or derived from elements), `bulk_modulus`, and `shear_modulus`.
- **Gap Analysis**: The dataset does *not* contain experimental yield strength or elongation. The spec explicitly pivots to DFT proxies (Bulk/Shear) to leverage this dataset. This is a valid substitution, not a gap.

### 1.2 Secondary Data: Periodic Descriptors
No external dataset download is required for elemental properties.
- **Source**: `mendeleev` Python library or a static internal mapping (e.g., `periodic_table.json`).
- **Desired Descriptors**: Atomic Radius, Electronegativity, Valence Electrons.
- **Rationale**: These are fundamental physical constants, not variable dataset entries. Hardcoding or using a lightweight library avoids unnecessary downloads and ensures reproducibility.

## 2. Methodology

### 2.1 Data Ingestion & Filtering (FR-001)
1. Load OQMD data from `materials-project/oqmd`.
2. Filter rows where `bulk_modulus` > 0 AND `shear_modulus` > 0 AND both are not null.
3. **Minimum Threshold Check**: If `len(valid_entries) < 500`, raise `SystemExit(1)` with a critical error.
4. **Schema Verification**: Explicitly check for the presence of `bulk_modulus` and `shear_modulus` columns. If missing, exit with error.

### 2.2 Composition Encoding (FR-002)
1. Parse composition strings (e.g., "Fe0.8Ni0.2") into elemental fractions.
2. For each element, retrieve:
   - Atomic Radius
   - Electronegativity
   - Valence Electrons
3. Construct feature vector:
   - Weighted average of descriptors (weighted by elemental fraction).
   - Weighted standard deviation of descriptors (to capture disorder).
   - Total number of elements (complexity).
4. **ilr Transform**: Apply Isometric Log-Ratio transform to elemental fractions to map simplex data to Euclidean space (required for LCE).
5. **Normalization**: Scale features using `StandardScaler`.

### 2.3 Surrogate Modeling (FR-003)
- **Algorithm**: Gradient Boosting Regressor (XGBoost or LightGBM).
- **Validation Strategy**: **Leave-One-System-Out (LOSO-CV)**.
  - "System" defined by the primary element(s) or a specific chemical family.
  - Iterate: Train on all systems except one; test on the held-out system.
  - **System Density Weighting**: Systems with < 20 points are flagged. The final R² metric is weighted by the inverse of the variance contribution of sparse systems to prevent skewing.
  - Aggregate R² scores.
- **Target**: R² > 0.6 on test sets (weighted).
- **Hyperparameters**: Grid search on `n_estimators`, `max_depth`, `learning_rate` within a 1-hour budget.

### 2.4 Pareto Optimization (FR-004)
- **Algorithm**: NSGA-II (via `deap` library).
- **Search Space**: Synthetic compositions generated within the **Convex Hull** of the training data.
- **Physical Bounds Validator**:
  - Calculate **Voigt Upper Bound** and **Reuss Lower Bound** for Bulk and Shear moduli for every synthetic point.
  - **Rule**: If `predicted_bulk > Voigt_bulk` OR `predicted_bulk < Reuss_bulk` (or similarly for Shear), the point is **rejected**.
- **Reliability Mask**:
  - Points with `uncertainty_variance` (from `model_validation_report.json`) above the 90th percentile are penalized in the fitness function.
- **Objectives**: Maximize Bulk Modulus, Maximize Shear Modulus.
- **Constraints**: Moduli > 0 (physical validity) AND within Voigt/Reuss bounds.

### 2.5 Decoupling Analysis (FR-005) - Local Correlation Estimation (LCE)
**Rejection of K-Means**: K-Means clustering on composition is rejected because it groups points by compositional similarity, which inherently groups points with similar property correlations, making "decoupling" a tautological artifact.

**New Method: Local Correlation Estimation (LCE)**
1. **ilr Transform**: Apply Isometric Log-Ratio transform to elemental fractions.
2. **Sliding Window**: For each point in the dataset, identify its **k-nearest neighbors** (k=50) in ilr-space.
3. **Local Correlation**: Calculate the Pearson correlation between Bulk and Shear moduli *within* this local neighborhood.
4. **Null Model (Stratified Permutation)**:
   - To validate significance, we construct a null distribution for each point.
   - **Procedure**: Shuffle the `bulk_modulus` values *only within the local neighborhood* of the point (preserving the local compositional density and property distribution).
   - Repeat 1000 times to generate a distribution of local correlations.
 - **Significance**: A point is "decoupled" if its observed local correlation is lower than [deferred] of the null distribution (p < 0.05) AND the local correlation is < 0.5.
5. **Output**: Identify regions (clusters of points) where the majority of points satisfy the decoupling criteria.

### 2.6 Sensitivity Analysis (FR-006)
- **Parameter**: Correlation threshold for defining "decoupled" (range [0.1, 0.9], step 0.1).
- **Metric**: `robustness_score` = Stability of decoupled region identification (e.g., Jaccard similarity of decoupled points) across the sweep.
- **Output**: `data/processed/sensitivity_analysis.csv`.

## 3. Compute Feasibility & Constraints

### 3.1 CPU-First Strategy
- **Models**: Gradient Boosting is highly efficient on CPU. XGBoost/LightGBM multi-threading will be utilized (2 cores).
- **NSGA-II**: Population size limited to 100-200 individuals; Generations limited to 50-100. Estimated runtime: < 30 mins.
- **LOSO-CV**: With [deferred] entries and ~10-20 systems, 10-20 folds. Each fold trains on [deferred] entries. XGBoost on 14k rows is trivial (< 5 mins). Total CV time: < 2 hours.
- **Memory**: All data fits in < 2 GB RAM.

### 3.2 GPU Escape Hatch (Not Required)
- No deep learning (Transformers/CNNs) is planned.
- **Current Plan**: Fully CPU-tractable. No CUDA dependencies.

## 4. Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied if testing multiple clusters simultaneously.
- **Power Analysis**: Minimum 500 entries ensures sufficient power for LOSO-CV.
- **Causal Claims**: None. All claims are associational (surrogate models).
- **Measurement Validity**: OQMD DFT values are the ground truth for this study.
- **Collinearity**: Elemental descriptors (radius, electronegativity) are correlated. The model will report feature importance, but independent effects will not be claimed for definitionally related features.
- **Null Model**: The stratified permutation test accounts for the smooth function of composition, ensuring that "decoupling" is not just noise in a small cluster.

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **OQMD (materials-project/oqmd)** | Only verified, open, programmatic source for Bulk/Shear moduli with correct schema. |
| **Gradient Boosting** | Best balance of accuracy and CPU speed for tabular data. |
| **LOSO-CV** | Standard for materials science to ensure generalization to new chemical systems. |
| **NSGA-II** | Proven algorithm for multi-objective optimization in materials design. |
| **Local Correlation Estimation (LCE)** | Replaces K-Means to avoid tautology; identifies decoupling based on local property variance, not spatial compactness. |
| **Stratified Permutation Test** | Required by SC-002 to validate statistical significance while accounting for local density. |
| **Voigt/Reuss Bounds** | Required by SC-003 to ensure physical consistency of synthetic points. |