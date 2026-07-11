# Research: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

## 1. Dataset Strategy

The project relies on two primary data sources for training and one for external validation. The spec requires the **ILThermo** dataset (provided locally) and the **SAPT2023** dataset (verified).

### 1.1 Verified Sources
Per the project constraints, only the following URLs are used. The ILThermo dataset is treated as a local data requirement due to access constraints, while SAPT2023 and dft23-full are verified HuggingFace datasets.

| Dataset Role | Source Name | Verified URL / Loader | Status / Adaptation |
| :--- | :--- | :--- | :--- |
| **Training (Energy)** | SAPT2023 | `datasets.load_dataset("sapt2023")` | **Verified**. Contains decomposed energy components (Electrostatic, Dispersion, Induction, Exchange) and SMILES. Used for training the three regressors. |
| **Training (Structure)** | ILThermo | `data/raw/ilthermo.csv` (Local) | **Local Requirement**. User must provide this CSV. Schema: `cation_smiles`, `anion_smiles`, `family_cation`, `family_anion`. |
| **Validation (DFT)** | DFT/SAPT High-Fidelity | `datasets.load_dataset("bio-datasets/dft23-full")` | **Verified**. Contains total interaction energies. Used for external validation (n=50 subset). |
| **Validation (DFT)** | DFT/SAPT High-Fidelity | `datasets.load_dataset("sdmattpotter/dftest61523")` | **Verified**. Backup source for validation set. |

### 1.2 Dataset Variable Fit Analysis
**Data Compatibility Check**:
- **SAPT2023**: Contains `smiles_cation`, `smiles_anion`, and decomposed energy labels (`electrostatic`, `dispersion`, `induction`, `exchange`). We map `induction` to `h_bond` (as a proxy for induction/H-bond coupling) or use `induction + dispersion` if specific H-bond labels are absent, but primarily rely on the explicit decomposition.
- **ILThermo**: Contains `cation_smiles`, `anion_smiles`, and structural families. Used to merge with SAPT2023 to ensure family stratification.
- **dft23-full**: Contains `smiles_cation`, `smiles_anion`, and `total_energy`. Used for validation by summing the three model predictions and comparing to `total_energy`.

**Geometric Feature Generation**:
- **Method**: ETKDG (RDKit) conformer generation from SMILES.
- **Validity**: If ETKDG fails for a pair, the row is **excluded** from the training set (logged). No ionic radii approximation or other proxy geometry is used. This ensures construct validity by guaranteeing that all geometric features represent actual spatial relationships derived from plausible 3D structures.
- **Outcome**: Only pairs with valid 3D geometries are included in the training table.

## 2. Methodology

### 2.1 Feature Engineering (FR-002)
- **Physicochemical**: Calculated via RDKit (`rdkit.Chem`) from SMILES. Includes:
  - Partial charges (Gasteiger).
  - Polarizability (approximate via volume).
  - H-bond donor/acceptor counts.
- **Graph Embeddings**: Morgan Fingerprints (radius=2, nBits=2048) for cation and anion separately, concatenated.
- **Geometric**: Generated via ETKDG from SMILES. Compute center-of-mass distance and orientation angles.
  - **Critical Constraint**: If ETKDG fails to generate a valid conformer, the row is **excluded**. No approximation is used. This prevents spurious correlations from invalid geometry proxies.

### 2.2 Modeling Strategy (FR-003, FR-004)
- **Algorithm**: XGBoost Regressor (`xgboost.XGBRegressor`).
- **Targets**: Three separate models for `Electrostatic`, `Dispersion`, `H-Bond` (mapped from SAPT2023).
- **Split**: Stratified 70/15/15 by cation/anion family (e.g., Imidazolium/BF4).
- **Hyperparameter Tuning**: Optuna with a time-limited timeout per trial. Search space: `max_depth` (lower bound), `learning_rate` [0.01-0.3], `n_estimators` [100-500].
- **CPU Constraint**: All operations forced to CPU. No GPU. Batch processing of features to stay within 3 GB RAM.
- **Sample Size Gate**: If the combined dataset yields < 1,000 valid pairs (with geometry), the pipeline halts with "Insufficient Sample Size". No modeling is attempted.

### 2.3 Analysis & Validation (FR-005, FR-006, FR-007)
- **MANOVA (Physical Trends)**: `statsmodels.stats.multivariate.manova` using Pillai's trace.
  - *Hypothesis*: Ground truth interaction energy components differ significantly across structural families.
  - *Dependent Variables*: **Ground truth** `electrostatic`, `dispersion`, and `h_bond` energies from the SAPT2023 dataset (not model predictions).
  - *Correction*: Multivariate approach inherently handles correlation between components (Electrostatic, Dispersion, H-Bond), satisfying FR-007.
  - *Note*: This tests whether the physical system exhibits family-based trends. Model performance (whether the model captures these trends) is evaluated separately.
- **Sensitivity Analysis (FR-006)**:
  - *Logic*: Iterate through a range of error thresholds $T$ in kcal mol⁻¹.
  - *Calculation*: For each threshold, calculate the **fraction of test predictions** where $|prediction - truth| \le T$.
  - *Robustness Flag*: Define `is_robust` = `True` if the fraction of predictions within the tolerance remains high (e.g., >90%) across the sweep, or if the drop-off in coverage between thresholds is minimal (<5%).
  - *Output*: A report containing the coverage fraction at each threshold and the boolean `is_robust` flag.
- **External Validation**: Compare ML predictions against the held-out DFT/SAPT subset (n=50) from dft23-full.
  - *Metric*: Sum of three model predictions vs. `total_energy` in dft23-full.
  - *Target*: MAE ≤ 0.5 kcal/mol, R² ≥ 0.80.

## 3. Statistical Rigor & Limitations

- **Multiple Comparison Correction**: Not strictly required for MANOVA as it tests the joint hypothesis. If post-hoc ANOVAs are run, Bonferroni correction will be applied.
- **Sample Size**: Power analysis is performed *before* modeling. If n < 1,000, the project halts. No "Case Study" fallback.
- **Causal Claims**: None. The study is observational/associational. Claims will be framed as "predictive correlations" or "statistical associations" between structure and energy.
- **Collinearity**: Physicochemical descriptors (e.g., polarizability and volume) may be correlated. Variance Inflation Factor (VIF) will be checked; highly collinear features (>10) will be dropped or combined.
- **Zero-Variance Targets**: If a family has zero dispersion energy, the regressor will be trained with a small epsilon added or a constant model fallback to prevent singular matrix errors.

## 4. Compute Feasibility

- **Memory**: Feature engineering on a dataset of estimated rows with high-dimensional fingerprints (e.g., thousands of dimensions) fits in a manageable memory footprint.
- **Time**: XGBoost on CPU for [deferred] rows is < 5 minutes. A conservative Optuna timeout is employed.
- **Disk**: Raw data (Parquet/JSONL) + processed CSV + models will fit in a manageable storage footprint.

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| Use XGBoost over Neural Nets | CPU constraints (no GPU); XGBoost is faster and more interpretable for tabular chemical data. |
| Stratified Split by Family | Ensures chemical diversity in train/test; prevents overfitting to specific ion types. |
| Separate Models per Component | Required by spec to isolate mechanism dominance; avoids multi-output complexity. |
| ETKDG for Geometry (Strict) | Ensures valid 3D structures. Rows failing ETKDG are excluded to avoid noise from approximations. |
| Local ILThermo | ILThermo is not publicly accessible via a simple URL; local provision is required. |
| Halt on Low Sample Size | Prevents invalid statistical claims (MANOVA) on insufficient data. |
| MANOVA on Ground Truth | Tests physical trends in the system, not model artifacts. |
| Sensitivity on Coverage Fraction | Correctly measures model reliability across error thresholds, avoiding the logical flaw of sweeping a constant MAE. |