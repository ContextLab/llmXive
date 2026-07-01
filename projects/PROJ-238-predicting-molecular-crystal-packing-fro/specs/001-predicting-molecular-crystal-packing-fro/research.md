# Research: Predicting Molecular Crystal Packing from Structural Descriptors

## Dataset Strategy

The project relies on the **Crystallography Open Database (COD)** as the primary source for crystal structures and unit cell parameters. As per the spec, the system must derive the `packing_coefficient` from unit cell volume and molecular volume.

**Verified Sources**:
The "Verified datasets" block provided by the system contains no pre-processed crystallographic datasets with unit cell parameters. Therefore, the project implements a **Direct Fetch Strategy** from the canonical COD source, which is the only valid mechanism to satisfy FR-001.

- **Primary Source**: Crystallography Open Database (COD) Bulk Download.
 - **URL**: ` (or the verified mirror `).
 - **Mechanism**: The `utils/data_loaders.py` script will fetch a sample of CIF files (e.g., via the COD API or a bulk tarball if available) and parse them for unit cell parameters ($a, b, c, \alpha, \beta, \gamma$) and atomic coordinates.
 - **Validation**: The script will verify that the downloaded CIFs contain valid unit cell parameters and organic small molecules.

- **Fallback**: If the COD fetch fails or yields insufficient data (N < 1000), the project will **not** substitute a dataset that lacks unit cell volumes (like the ChemBl datasets), as this would make the target variable (`packing_coefficient`) impossible to derive. The project will pause and flag the data gap.

**Critical Mismatch Resolution**: The provided "Verified Sources" block lists code-generation and protein-ligand datasets (e.g., MAESTRO, ChEMBL) that lack unit cell volume. The plan explicitly rejects these for the primary target variable and relies on the direct COD fetch mechanism as the verified source.

## Methodology

### 1. Data Ingestion & Descriptor Computation (FR-001, FR-002, FR-007)
- **Source**: COD (direct fetch).
- **Process**:
 1. Download CIF files for a random sample of organic small molecules.
 2. Parse CIF for unit cell parameters to calculate Unit Cell Volume ($V_{cell}$).
 3. Extract SMILES or 3D coordinates.
 4. Use RDKit to:
 - Add hydrogens (geometric).
 - Compute Molecular Volume ($V_{mol}$), Surface Area, Dipole Moment, HBA, HBD, PSA.
 - Derive `packing_coefficient` = $V_{mol} / V_{cell}$.
 5. **Missing Data Handling**:
 - If auxiliary descriptors (e.g., Dipole) are missing: Impute with the **training set median** and flag the row.
 - If `packing_coefficient` (target) is missing: **Exclude** the entry from training and log the count.
 6. Filter: Exclude if $V_{cell} = 0$, `packing_coefficient` $\notin [0.5, 1.0]$, or molecular weight > 1000 Da.

### 2. Data Splitting (FR-003)
- **Strategy**: Stratified split by **packing_coefficient** (target variable).
 - *Rationale*: Stratifying by Molecular Weight (as originally proposed) stratifies by the numerator of the target, potentially biasing the split. Stratifying by the target ensures the model learns the inference of $V_{cell}$ across the full range of packing densities.
- **Ratio**: [deferred] Train, [deferred] Validation, [deferred] Test.
- **Validation**: Kolmogorov-Smirnov test ($p > 0.05$) on the **target distribution** to confirm similarity across splits.

### 3. Model Training (FR-004)
- **Algorithms**: Random Forest Regressor, Gradient Boosting Regressor.
- **Baseline**: Mean Predictor (predicts mean of training set).
- **Constraints**: CPU-only, `n_jobs=1` or `2`, `random_state=42`.
- **Hyperparameters**: Default scikit-learn values to ensure reproducibility and speed.
- **Control Analysis**: Train a secondary model **excluding** `Volume` and `Surface Area` to test if interaction-specific descriptors (Dipole, H-bonds) drive packing efficiency. This addresses the tautology risk.

### 4. Evaluation & Statistical Rigor (FR-005, SC-001, SC-005)
- **Metrics**: R², MAE, RMSE.
- **Significance**: Paired t-test between model predictions and baseline predictions on the *same* test set.
- **Multiple Comparison Correction**: Since 2 models (RF, GB) are compared against 1 baseline, apply **Bonferroni correction** ($\alpha_{corrected} = 0.05 / 2 = 0.025$).
- **Causal Framing**: Explicitly state that results are **associational**. No randomization of crystal conditions exists.

### 5. Feature Importance & Sensitivity (FR-006, SC-003)
- **Feature Importance**: Use **Permutation Importance** (not Gini) to account for collinearity (e.g., Volume vs Surface Area). This measures the drop in performance when a feature's values are shuffled, avoiding the "masking" effect of collinearity.
- **Sensitivity Analysis**: Perform **Leave-One-Feature-Out (LOFO)** analysis.
 - *Method*: Remove one feature at a time, retrain, and measure R² drop.
 - *Target*: Document R² variation; acknowledge that removing Volume may cause a large drop due to geometric definition.
- **Collinearity Check**: Report correlation matrix of descriptors. If `Volume` and `Surface Area` are highly correlated, acknowledge they may not represent independent effects.

### 6. Interaction Classification (FR-008)
- **Method**: Geometric criteria from CIF.
 - H-bond: Distance < 3.5Å, Angle > 150°.
 - Classify as "H-bond dominated", "Van der Waals dominated", etc.
- **Framing**: This classification is a **heuristic proxy** based on geometric cutoffs, not absolute physical truth. The plan will report the consistency of this heuristic (bootstrapped 95% CI) but will not claim it as ground truth.
- **Limitation**: Acknowledge that geometric cutoffs are approximations and may not capture all interaction types.

## Statistical Rigor Checklist

- [x] **Multiple Comparison Correction**: Bonferroni applied for RF vs Mean and GB vs Mean.
- [x] **Power/Sample Size**: Acknowledgement of limitation. With N ~1000, power is moderate for R² detection.
- [x] **Causal Assumptions**: Framed as associational prediction. No causal claims.
- [x] **Measurement Validity**: RDKit descriptors are standard; H-bond geometric criteria are standard in crystallography.
- [x] **Collinearity**: Will be reported in `research.md` and `results/`; Permutation Importance used.
- [x] **Tautology Control**: Control analysis (excluding Volume/SA) included.

## Compute Feasibility

- **Hardware**: 2 CPU, 7 GB RAM.
- **Strategy**:
 - Limit dataset to [deferred]-2,000 rows.
 - Use `scikit-learn` (CPU optimized).
 - Avoid deep learning.
 - Process data in chunks if necessary.
- **Runtime**: Est. 1-2 hours for full pipeline.

## Limitations

- **Descriptor Validity**: RDKit computes isolated molecular volume, which may differ from effective crystal volume due to conformational changes. The control analysis will test if non-geometric descriptors add predictive power.
- **Interaction Classification**: Geometric cutoffs are heuristic; the classification is a proxy, not ground truth.
- **Data Source**: Reliance on direct COD fetch; if the API/mirror is unavailable, the pipeline cannot proceed.
