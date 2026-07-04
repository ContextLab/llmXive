# Research: Predicting Material Stability using Machine Learning and DFT Calculations

## Research Question
To what extent do local coordination environment features (Voronoi statistics, bond-length distributions) improve the prediction of **DFT formation energy** and the **mathematical classification** of metastable phases (based on DFT-derived convex hull distance) compared to bulk compositional descriptors (Magpie features) for Li-rich rock-salt oxides?

*Note: The classification task is a self-consistency check of the DFT data and hull algorithm, not an empirical validation against experimental synthesis.*

## Dataset Strategy

The project relies on the Open Quantum Materials Database (OQMD). The specific dataset must contain Li-rich oxides with rock-salt structures and fully relaxed DFT energies.

| Dataset Name | Source URL (Verified) | Description | Usage |
|:--- |:--- |:--- |:--- |
| **OQMD Completion (Scalars)** | ` | Contains scalar properties: formation energy, hull distance. | Primary source for ground truth formation energy (`formation_energy_per_atom`) and hull distance. |
| **OQMD Structures (CIFs)** | ` | Contains crystal structure files (CIF) and composition data. | Source for structural data (lattice vectors, atomic positions) required to compute Voronoi tessellation. |
| **OQMD Targets (Metadata)** | ` | Contains formation energies and basic metadata. | Fallback for metadata if primary sources fail. |

**Dataset Fit Verification**:
- **Required Variables**: Composition, Crystal Structure (lattice vectors, atomic positions), Formation Energy.
- **Status**: The verified OQMD sources contain these variables, but they are split across different files (scalars vs. structures).
- **Filtering Strategy**: The `download_data.py` script will:
 1. Load scalar data and filter for Li-rich oxides.
 2. **Crucial**: Instead of strict Space Group 225 filtering, it will target structures with a **rock-salt topology** (coordination number ~6 for cations/anions) to include disordered phases (DRX) that may have lower symmetry.
 3. Retrieve corresponding structural files (CIFs) for the filtered IDs.
 4. **Data Integrity Check**: Verify that every retained entry has valid lattice vectors and atomic positions. If structural data is missing, the entry is excluded and logged.
- **Risk Mitigation**: If fewer than 100 samples are found after filtering, the system logs a warning and proceeds, but the `sensitivity_analysis` will flag the low sample size as a power limitation (Edge Case handling).

## Methodological Approach

### 1. Data Preprocessing
- **Download & Filter**: Fetch OQMD data, filter for Li-rich rock-salt structures (topological criteria).
- **Data Join**: Join scalar properties with structural data using `material_id`.
- **Imputation**: Missing bond lengths or degenerate Voronoi cells will be imputed with the dataset median or skipped, with counts logged.

### 2. Feature Engineering
- **Bulk Descriptors (Magpie)**: Computed using `matminer` (or `pymatgen` equivalents) to generate elemental property statistics (mean, range, deviation) for the composition.
- **Local Coordination Descriptors**:
 - **Voronoi Tessellation**: Computed using `pymatgen.analysis.voronoi_tessellation`. Metrics include coordination number, face area, and solid angle.
 - **Bond-Length Histograms**: Distribution of bond lengths for each unique cation-anion pair.
 - **Aggregation Strategy (Fixed-Size Vector)**:
 - **Voronoi Stats**: Aggregated via weighted averaging by coordination number.
 - **Bond-Length Histograms**: Converted to fixed-size vectors using statistical moments (mean, std, skewness, kurtosis) and percentiles (10th, 50th, 90th).
 - **Result**: A single fixed-length vector per material.

### 3. Model Training
- **Algorithm**: Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`).
- **Baseline Model**: Trained on Magpie features only.
- **Augmented Model**: Trained on Magpie + Local Coordination features.
- **Hyperparameter Tuning**: Grid search or randomized search on a validation split.
- **Constraints**: Models trained on CPU. If dataset size exceeds available RAM, a random sample will be taken to ensure feasibility.

### 4. Evaluation & Classification
- **Regression Metrics**: MAE, RMSE, R².
- **Classification (Self-Consistency Check)**:
 - **Ground Truth**: Distance to convex hull calculated via `pymatgen.analysis.phase_diagram.PhaseDiagram`.
 - **Cohort Stratification**: The analysis will focus on a **"Near-Hull" cohort** (0.00 < dist ≤ 0.05 eV/atom) to isolate the signal for the research question, distinguishing it from deeply metastable phases.
 - **Metrics**: AUC-ROC, Precision, Recall, F1 calculated specifically for the Near-Hull cohort.
- **Sensitivity Analysis**: Threshold sweep across {0.04, 0.05, 0.06} eV/atom to assess robustness within the Near-Hull cohort.

## Statistical Rigor & Assumptions

- **Observational Nature**: The study is observational; findings are framed as associational. No randomization of cation ordering exists in the dataset.
- **Multiple Comparisons & Significance**: As the primary comparison is between two models (Baseline vs. Augmented) on the same test set, a **permutation test** will be used to assess the significance of the MAE reduction.
 - **Method**: Generate a null distribution by shuffling model assignments a sufficient number of times. Calculate the p-value based on the observed delta-MAE.
 - **Rationale**: This avoids normality assumptions required by t-tests and handles heavy-tailed error distributions common in materials science.
- **Power Limitation**: If the filtered dataset is small (<500 samples), the study will explicitly acknowledge reduced statistical power in the final report.
- **Collinearity Analysis**:
 - **Method**: Calculate Variance Inflation Factors (VIF) for the feature set before model training.
 - **Handling**: If VIF > 5 for any feature, the plan will report the correlation structure and avoid claiming "independent effects" for highly collinear features. The focus will shift to the aggregate predictive gain of the feature set.
- **Circularity & Scope**:
 - **Acknowledgement**: The classification task uses DFT-calculated distance to the convex hull as the ground truth. This is a self-consistency check of the DFT model's predictive power for stability, not a substitute for experimental synthesis data.
 - **Implication**: A negative result (poor AUC) would imply a bug in the feature engineering or the hull calculation, not a failure of the physics hypothesis. The "improvement" metric measures the model's ability to fit the non-linearities of the DFT energy surface better than bulk features alone.
- **Measurement Validity**: `pymatgen`'s `PhaseDiagram` is the standard for convex hull calculations in computational materials science.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Gradient Boosting** | Robust to non-linearities, handles mixed feature types, and computationally efficient on CPU compared to deep learning. |
| **Use `pymatgen` for Hull** | Industry standard library; ensures consistency with DFT reference energies. |
| **Threshold Sweep {0.04, 0.05, 0.06}** | Addresses the uncertainty in DFT formation energy calculations and the arbitrary nature of the 0.05 eV/atom cutoff. |
| **CPU-Only Execution** | Mandatory for compatibility with free-tier CI runners (2 cores, 7 GB RAM). |
| **Permutation Test** | Necessary to handle non-normal error distributions in materials science. |
| **VIF Analysis** | Required to quantify collinearity and avoid invalid claims of independent effects. |
| **Near-Hull Cohort** | Focuses the classification task on the specific range of interest (0.00-0.05 eV/atom) to avoid diluting the signal with deeply metastable phases. |