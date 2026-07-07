# Research: Predicting Plant Drought Tolerance from RSA Data

## Dataset Strategy

This project relies on two primary data sources: root images for RSA extraction and trait databases for physiological validation.

| Dataset | Description | Verified Source URL | Usage |
|:--- |:--- |:--- |:--- |
| **NPPN (Root Images)** | Root System Architecture images for trait extraction. | **NO verified source found** (Per prompt instructions, no URL cited). | **Critical**: If no real images are found in `data/raw/`, the pipeline halts. No synthetic data is used for primary analysis. |
| **RSA (Parquet)** | Pre-extracted RSA metrics (benchmark). | ` | Used **only** for unit testing pipeline format compatibility. Not used for biological analysis. |
| **TRY (Traits)** | Physiological traits (stomatal conductance, photosynthesis) for species. | ` | Primary source for `PhysioTrait` (gs, A) to correlate with RSA. |
| **TRY (Alternative)** | Additional TRY data or test sets. | ` | Fallback if primary TRY URL fails or for specific test subsets. |
| **PGLS (Phylogeny)** | Phylogenetic trees for species correction. | **Open Tree of Life API** (`) | **Mandatory**: Script `fetch_phylogeny.py` uses `requests` to fetch a supertree. Fallback: Phylogenetic Eigenvector Regression (PVR) using taxonomic hierarchy if API fails. |

### Dataset Fit Analysis
- **Variable Availability**: The TRY dataset (`try.csv`) is expected to contain `species`, `stomatal_conductance`, and `photosynthesis_rate`. If specific stress conditions are missing, the plan will filter for "water_stress" flags or default to general physiological rates with a "limitation" disclaimer.
- **NPPN Gap**: Since no verified URL exists for NPPN raw images, the pipeline **must** halt if no local images are provided. The research question cannot be answered with simulated data.
- **PGLS Strategy**: The Open Tree of Life API will be queried for the species in the merged dataset. If a tree cannot be constructed for >80% of species, the pipeline will use a **Phylogenetic Eigenvector Regression (PVR)** approach, deriving a distance matrix from taxonomic hierarchy (Genus/Family) as a proxy for phylogeny, satisfying the "equivalent correction" requirement of FR-010.

## Methodology & Statistical Rigor

### 1. Data Ingestion & Cleaning (FR-001, FR-002)
- **Image Processing**: Use `opencv-python-headless` and `scikit-image` for thresholding and skeletonization to extract depth, branching density, and surface area.
- **Missing Data**: Listwise deletion for species missing in either RSA or TRY datasets. If sample size drops <30, the study will report a "power limitation" warning.
- **Data Gap Protocol**: If `data/raw/nppn_images/` is empty, the pipeline exits with `Error: No real root images found. Primary analysis cannot proceed.`

### 2. Collinearity & Size Control (FR-006, FR-010)
- **Size Control**: Include `total_root_length` as a covariate in all models to distinguish architectural effects from allometric size effects.
- **VIF Check**: Calculate Variance Inflation Factor (VIF) for all RSA predictors.
- **PCA**: If VIF > 5 for any predictor, apply PCA to the RSA features (after controlling for size). The resulting principal components (PCs) will be used as inputs for regression to ensure orthogonality.
- **Reporting**: The report will explicitly state which variables were collinear and how they were transformed.

### 3. Statistical Modeling (FR-003, FR-004, FR-009)
- **Primary Target**: "Physiological State" (stomatal conductance/photosynthesis). **Not** "Drought Tolerance" unless an independent proxy is found.
- **Regression**:
 - **Model 1**: Multiple Linear Regression (MLR) with PCA-transformed RSA features + Size Control predicting stomatal conductance.
 - **Model 2**: Random Forest Regression (RFR) for non-linear relationships (Exploratory only).
 - **Validation**: **Leave-One-Species-Out (LOSO)** cross-validation. Metric: $R^2$. *Note: 5-fold CV is insufficient for N<100 and risks species leakage.*
 - **Correction**: Bonferroni correction applied to p-values if multiple hypotheses are tested.
- **Causal Framing**: All results will be framed as "associational." No causal claims ("causes," "leads to") will be made.
- **Phylogeny**: PGLS will be implemented using the tree fetched from the Open Tree of Life API. If the tree is incomplete, PVR (using taxonomic hierarchy) will be used as an equivalent correction.

### 4. Classification & Sensitivity (FR-005, FR-007, FR-008)
- **Conditional**: Classification is **only** performed if an independent tolerance proxy (e.g., survival rate, biomass loss) is found in the data.
- **Binarization**: If a proxy exists, the continuous metric is binarized using the median value as the threshold.
- **Classification**: Random Forest Classifier to predict the binary class. Metric: F1-score.
- **Sensitivity Analysis**: Sweep the classification threshold by ±0.05 (and ±0.1). Plot F1-score, Accuracy, and AUC against the threshold.
- **N/A Case**: If no independent proxy exists, the classification section is marked "N/A" with a justification that the research question is framed as "Physiological State Prediction" (Regression).

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (CPU, ample RAM).
- **Strategy**:
 - **Image Processing**: Process images in batches to stay under 7 GB RAM.
 - **Modeling**: Use `scikit-learn` with `n_jobs=2`. Limit `RandomForest` to `n_estimators=100` and `max_depth=10` to prevent overfitting and ensure speed.
 - **Data Size**: If the dataset exceeds ~500MB, sampling will be applied to ensure runtime < 6 hours.
 - **No GPU**: All libraries (`torch`, `tensorflow`, `bitsandbytes`) are excluded. `opencv-python-headless` is used to avoid GUI dependencies.
 - **Phylogeny**: `requests` and `treelib`/`ete3` are CPU-tractable.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **LOSO CV over 5-fold** | N=30-100 is too small for 5-fold. LOSO maximizes data usage and respects species non-independence. |
| **Median split removed** | Median splits on the target variable create circular validation. Classification is only valid with an independent proxy. |
| **Open Tree of Life API + PVR Fallback** | Static tree files are unreliable. Fetching via API ensures the most up-to-date phylogeny. PVR fallback ensures FR-010 is met even if API fails. |
| **Halt on missing images** | Using synthetic data invalidates the biological hypothesis. The pipeline must fail gracefully rather than produce false positives. |
| **Size Control** | RSA traits are definitionally correlated with plant size. Controlling for size ensures the signal is architectural, not allometric. |
| **Reframed Research Question** | "Drought Tolerance" is a capacity; "Physiological State" is an instantaneous measure. The study predicts state unless a capacity proxy is found. |