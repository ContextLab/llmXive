# Research: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## 1. Problem Definition & Hypothesis

**Problem**: Quantify the information loss incurred when predicting quantum chemical descriptors (dipole moment, HOMO, LUMO) using 2D topological representations (Morgan fingerprints) versus 3D geometric representations (graph features with coordinates).

**Hypothesis**: 2D representations will perform comparably to 3D representations for global, scalar properties (HOMO, LUMO) but will exhibit a significant "failure boundary" (relative error increase ≥ 5% MESI) for directional, vector-dependent properties (dipole moment) due to the lack of explicit geometric information.

## 2. Dataset Strategy

The project utilizes the **QM9 dataset**, a standard benchmark containing [deferred] small organic molecules with DFT-calculated properties.

### Verified Sources
Per the project's verified dataset constraints, the primary data source is the QM9 dataset available via HuggingFace, which provides the necessary 3D coordinates and DFT labels.

| Dataset | Source URL | Content | Relevance |
|---------|------------|---------|-----------|
| QM9 (Parquet) | ` | Contains SMILES, 3D coordinates (x, y, z), and DFT properties (mu, HOMO, LUMO). | Primary source for features and labels. |

*Note: The Harvard Dataverse URL (doi:10.7910/DVN/28075) mentioned in FR-001 is the original source, but the implementation uses the verified HuggingFace Parquet source to ensure reproducibility and successful download in CI. The feature extraction logic reads Parquet directly, bypassing the need for local XYZ parsing.*

### Data Variables & Fit
- **Predictors**:
 - 2D: Morgan fingerprints (radius=2, nBits=2048).
 - 3D: Atomic numbers, hybridization, bond distances, angles, dihedrals (derived from XYZ).
- **Outcomes**:
 - `mu` (Dipole moment magnitude).
 - `homo` (Highest Occupied Molecular Orbital energy).
 - `lumo` (Lowest Unoccupied Molecular Orbital energy).
- **Fit Check**: The QM9 dataset explicitly contains `mu`, `homo`, and `lumo` columns, confirming perfect variable fit for the study requirements.

## 3. Methodology

### 3.1 Feature Engineering
1. **2D Features**:
 - Convert SMILES to RDKit Mol objects.
 - Generate Morgan fingerprints (radius=2, nBits=2048).
 - *Rationale*: Standard topological descriptor; computationally cheap; lacks 3D geometry.
2. **3D Features**:
 - Parse XYZ coordinates from the dataset.
 - Construct a molecular graph where nodes = atoms (features: atomic number, hybridization) and edges = bonds.
 - Calculate geometric invariants: pairwise distances, bond angles, dihedral angles.
 - *Rationale*: Encodes explicit spatial information required for vector properties. These features are geometric invariants and do not directly encode the dipole vector components, avoiding a trivial identity mapping. The model must learn the complex relationship between geometry and electronic properties.

### 3.2 Model Architecture
- **Algorithm**: Random Forest Regressor (Scikit-Learn).
- **Rationale**:
 - CPU-tractable (unlike GNNs or Transformers).
 - Robust to high-dimensional sparse data (fingerprints).
 - Non-parametric; no need for complex hyperparameter tuning beyond the specified grid.
- **Configuration**:
 - `n_estimators`: {100, 500}
 - `max_depth`: {10, 20, None}
 - **Cross-Validation**: 5-fold stratified (by property magnitude bins to ensure distribution alignment).
 - *Justification for Fixed Grid*: The fixed grid (FR-003) is sufficient for a comparative study as Random Forests are robust to hyperparameter variations for this problem type, and the grid covers the transition from underfitting to overfitting.

### 3.3 Statistical Rigor & Metrics
- **Primary Metrics**: Mean Absolute Error (MAE), Root Mean Square Error (RMSE).
- **Comparative Metric**: Relative Error Increase (REI) = `(MAE_2D - MAE_3D) / MAE_3D`.
- **Statistical Testing**:
 - **Strict Intersection Filter**: Before testing, drop any molecule where 3D feature extraction fails, ensuring the paired error vectors contain only molecules present in both sets.
 - **Non-Parametric Test**: Wilcoxon signed-rank test will be used as the primary test for error differences to account for potential non-normality and heteroscedasticity. Paired t-test will be used as a secondary check.
 - **Multiple Comparison Correction**: Since three distinct descriptors are tested (mu, homo, lumo), the Benjamini-Hochberg procedure will be applied to control the False Discovery Rate (FDR).
- **Sample Size & Power**:
 - The dataset size is large, but the implementation will use a subset to fit memory constraints.
 - *Power Limitation*: With ~10k samples, the test has >99% power to detect even small effect sizes. To avoid Type I error inflation from trivial differences, a **Minimum Effect Size of Interest (MESI)** of [deferred] relative error increase is defined. Statistical significance is only considered a "failure boundary" if the effect size exceeds this MESI.
- **Causal Inference**: Observational study. Claims will be framed as "associational" regarding representation quality, not causal effects of molecular structure.
- **Collinearity**: 2D fingerprints and 3D features are distinct representations. No direct collinearity between predictors within a single model, but the *target* properties are correlated. This is handled by modeling each property separately.

### 3.4 Computational Feasibility (CPU-Only)
- **Constraint**: 2 CPU, 7GB RAM, 6 hours.
- **Strategy**:
 - **Data Subset**: If memory > 6.5 GB during feature extraction, the pipeline will automatically downsample to a smaller subset (e.g., 5k molecules) while maintaining chemical diversity distribution.
 - **Parallelism**: Use `n_jobs=2` in Scikit-Learn to utilize both CPU cores.
 - **No GPU**: Explicitly avoided. Random Forest is inherently parallelizable on CPU.
 - **Memory Management**: Process molecules in batches; clear intermediate objects from memory using `del` and `gc.collect()`.

### 3.5 Theoretical Lower Bound (FR-007)
- **Definition**: The "theoretical lower bound" is defined as the **Mean Predictor Error** (predicting the mean of the training set for all inputs). This serves as a non-trivial baseline for the complexity of the mapping, avoiding the tautology of "identity mapping" when features are derived from the same geometry as the target.
- **Calculation**: Train a simple model that outputs the mean of the training labels for all test inputs. Calculate MAE/RMSE against the test set.

## 4. Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| **Use HuggingFace QM9** | Verified source; direct parquet access; contains all required variables. | Harvard Dataverse (no verified URL in block); local manual download (not reproducible in CI). |
| **Random Forest** | CPU-tractable; handles high-dimensional sparse data well; robust baseline. | Graph Neural Networks (GNNs) (require GPU for reasonable speed; complex to implement); Deep Learning (overkill for this tabular/graph problem). |
| **Downsampling Strategy** | Ensures CI success; prevents OOM errors. | Static subset size (risks OOM if hardware varies; or under-utilization). |
| **Paired t-test + BH Correction** | Controls for multiple comparisons; directly tests the "failure boundary" hypothesis. | Unpaired t-test (less powerful for paired data); no correction (inflated Type I error). |
| **Strict Intersection Filter** | Ensures valid paired t-test by removing molecules with missing 3D features. | Imputation strategies (risk introducing bias). |
| **Wilcoxon Signed-Rank Test** | Robust to non-normality and heteroscedasticity in molecular error distributions. | Standard paired t-test (assumes normality). |
| **MESI ([deferred])** | Prevents trivial differences from being flagged as significant due to large N. | Relying solely on p-value. |
| **Mean Predictor Error** | Provides a non-trivial baseline for the theoretical lower bound. | Identity mapping error (tautological when features derive from target geometry). |