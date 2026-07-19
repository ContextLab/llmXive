# Research: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## Executive Summary

This research investigates the extent to which 2D topological representations (Morgan fingerprints) can approximate the predictive power of 3D geometric representations (DFT-optimized graphs) for molecular descriptors in the QM9 dataset. The core hypothesis is that while 2D features suffice for global properties (e.g., HOMO/LUMO), they fail for directional properties (e.g., dipole moment) due to the lack of explicit spatial information. The study is bounded by the computational constraints of a GitHub Actions free-tier runner (CPU-only, 7 GB RAM), necessitating a robust data sampling strategy.

## Dataset Strategy

The project relies on the QM dataset, a standard benchmark in quantum chemistry containing a large collection of small organic molecules with DFT-calculated properties.

### Verified Datasets

| Dataset Name | Source Type | Verified URL / Loader | Variables Available | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **QM9 (Parquet)** | HuggingFace Mirror | `datasets.load_dataset("lisn519010/QM9")` | `smiles`, `xyz` (3D coords), `mu` (dipole), `homo`, `lumo` | Verified source for QM9. Contains all required DFT labels. The Harvard Dataverse (doi:10.7910/DVN/28075) is the canonical source, but this HF mirror is used for programmatic CI access. |
| **QM9 (Subset)** | Internal Derivation | `data/raw/qm9_subset.parquet` | Same as above | Derived by streaming the full dataset and applying a **stratified random sample** to fit memory constraints. |

**Note on Harvard Dataverse**: The spec references `doi:10.7910/DVN/28075`. As per the "Verified datasets" block, no direct URL is provided for the Harvard source. We utilize the HuggingFace dataset `lisn519010/QM9` which is a verified mirror of this data, ensuring bit-for-bit compatibility of the `.xyz` and property fields required for the analysis.

### Data Availability & Feasibility

- **Accessibility**: The dataset is available via the `datasets` library, allowing streaming (`streaming=True`) to avoid loading the full dataset into memory at once.
- **Variable Fit**: The dataset contains `smiles` (for 2D), `xyz` (for 3D), and the target labels `mu` (dipole), `homo`, and `lumo`. This perfectly matches the requirements of FR-002.
- **Memory Constraints**: The full dataset (large uncompressed size) exceeds the available RAM limit.
  - **Strategy**: Implement a streaming loader that reads the dataset in chunks. A **binary search** over sample size `N` (bounds: min=1000, max=134000) will be performed to find the maximum `N` where 3D graph construction + feature matrix storage < 6.5 GB RAM.
  - **Stratification**: The sampling will be **stratified** by target variables (mu, homo, lumo) and atom count to preserve chemical diversity and prevent selection bias.
  - **Fallback**: If the maximum feasible `N` is too small for statistical significance (e.g., < 1,000), the plan will acknowledge the power limitation in the final report but proceed with the largest possible valid sample.
- **Streamability Verification**: Before full extraction, a verification step will confirm that the `xyz` column in the HF mirror is streamable and parseable by RDKit. If the column format is incompatible (e.g., flattened array), the plan will fall back to a pre-processed subset or a different loader.

## Methodology

### 1. Feature Extraction

- **2D Features**: Morgan Fingerprints (Radius=2, 2048 bits) generated from `smiles` using RDKit.
- **3D Features**: Graph representation where nodes are atoms (features: atomic number, hybridization) and edges are bonds (features: distance bins, bond angles). Distance, angle, and dihedral features are computed from the `xyz` coordinates.
- **Alignment**: Features and labels are aligned by molecule ID. Molecules with missing labels or invalid geometry are dropped.
- **Sampling**: A **stratified random sample** is drawn based on target variables and atom count. A binary search (min=1000, max=134000) determines the maximum sample size fitting within 6.5 GB RAM.
- **Fallback Strategy**: If the initial streamability check fails (e.g., `xyz` column cannot be streamed), the system will switch to a pre-processed, chunked parquet loader to ensure the binary search can proceed without OOM.
- **Schema Verification**: A specific check will be performed to ensure the `xyz` column in the HF mirror matches the expected schema (array of arrays) or is transformed from the alternative format (object with x/y/z arrays) before processing.

### 2. Model Training

- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Justification**: RF is robust to high-dimensional sparse data (fingerprints) and non-linear relationships. It runs efficiently on CPU and does not require GPU acceleration. For 3D features, RF is chosen to ensure a fair, non-parametric comparison with 2D fingerprints, avoiding the complexity and hyperparameter sensitivity of GNNs which could bias the comparison.
- **Hyperparameters**: Grid search over `n_estimators` (e.g., varying magnitudes) and `max_depth` (10, 20, None).
- **Validation**: 5-fold Cross-Validation (as per verified fact `cross fold pipeline training use validation = 5`).
- **Fold Consistency**: A **single fixed random seed** is used for the CV splitter to ensure **identical fold assignments** for both 2D and 3D models, ensuring errors are paired on the same molecules.
- **Compute**: Trained on the sampled subset. Runtime monitored to ensure < 6 hours.

### 3. Comparative Analysis & Failure Boundary

- **Metrics**: Mean Absolute Error (MAE) and Root Mean Square Error (RMSE) for Dipole, HOMO, LUMO.
- **Baseline**: Calculate the **Mean Predictor Error** (Zero-Order Baseline: predicting the mean of the training set) as per FR-007. This operationalizes the "identity mapping error" for this project, providing a theoretical lower bound to contextualize model performance.
- **Relative Error Increase (REI)**: Calculated as `(MAE_2D - MAE_3D) / MAE_3D`.
  - **Guardrail**: If `MAE_3D < 0.01` (near-zero), the REI metric is flagged as 'unstable' and the analysis defaults to comparing **Absolute Error Differences (AED)** instead to prevent division-by-zero artifacts.
- **Direct Ground Truth Comparison**: Both models' errors are compared directly against the DFT ground truth (MAE vs DFT) to validate that the 2D model's failure is not circular but relative to the true target.
- **Statistical Testing**:
  - **Hypothesis**: The 2D model performs significantly worse than the 3D model for directional properties.
  - **Pre-check**: Perform a **Shapiro-Wilk normality test** on per-molecule errors (2D vs 3D).
  - **Test Selection**: If Shapiro-Wilk p < 0.05 (non-normal), use **Wilcoxon signed-rank test**. Otherwise, use **paired t-test**.
  - **Correction**: Bonferroni correction applied for multiple tests (Dipole, HOMO, LUMO), setting significance threshold to `0.05` divided by the number of tests.
- **Failure Boundary Definition**: A descriptor is considered to have "failed" 2D approximation if **REI ≥ 10% AND p-value < 0.0167**. This logic requires both a meaningful effect size and statistical significance.
- **Scope Qualification**: Explicitly state that the results are a **theoretical lower bound** due to the use of DFT-optimized geometries, and not a practical failure boundary for noisy 3D predictions.

## Decision Rationale

| Decision | Rationale | CPU/GPU Fit |
| :--- | :--- | :--- |
| **Random Forest** | Robust, interpretable, no GPU needed, handles mixed feature types. Fair comparison for 3D vs 2D. | **CPU-First**: Runs efficiently on 2 cores. |
| **QM9 (HF Mirror)** | Only verified, programmatic source available. Contains all required variables. | **CPU-First**: Streaming allows processing within RAM limits. |
| **Conditional Statistical Test** | Ensures robustness against non-normal error distributions while maintaining Spec alignment. | **CPU-First**: Negligible compute cost. |
| **Dynamic Downsampling** | Necessary to fit 3D graph construction into 7 GB RAM. | **CPU-First**: Ensures feasibility on free-tier runner. |
| **Stratified Sampling** | Prevents selection bias and preserves chemical diversity during downsampling. | **CPU-First**: Ensures external validity. |

## Limitations

- **Sample Size**: The feasible sample size is constrained by RAM, potentially limiting the statistical power for subtle effects.
- **Dataset Scope**: QM9 contains only small organic molecules; results may not generalize to larger or inorganic systems.
- **3D Input**: The 3D model uses DFT-optimized geometries, which are perfect. In real-world scenarios, 3D structures are often predicted (and thus noisy), which would further degrade 3D model performance. This is a theoretical lower bound on 2D vs 3D gap.