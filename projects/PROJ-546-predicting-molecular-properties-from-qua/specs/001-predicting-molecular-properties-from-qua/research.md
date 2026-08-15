# Research: Predicting Molecular Properties from Quantum Chemical Calculations

## Summary

This research validates the feasibility of using semi-empirical (DFTB+) and high-level (Psi4) quantum chemical descriptors to predict experimental molecular barrier heights. The study addresses the computational trade-off between accuracy and speed by comparing two Random Forest models trained on different descriptor sets, using a paired t-test to evaluate statistical significance.

**Scientific Scope Clarification**: The comparison is explicitly defined as "DFTB+ on DFTB+ geometry" vs "Psi4 on DFTB+ geometry". This tests the sensitivity of the energy functional to geometry errors. Optimizing geometries at the DFT level is out of scope due to resource constraints (Constitution Principle VII). The experimental barriers may include solvation effects, while calculations are gas-phase; this missing physics is a known limitation of the validation target.

## Dataset Strategy

### Primary Dataset
- **Source**: Experimental barrier dataset from Zenodo (Accession ID: [ID from Idea.md], URL: [URL from Idea.md]).
- **Access**: Programmatic download via `requests` or `zenodo_get` (if API available).
- **Verification**: SHA-256 checksum verification against the Zenodo record metadata before processing (Constitution Principle III). Status logged to `logs/verification.log`.
- **Content**: `smiles`, `experimental_barrier`, `molecule_id`.
- **Feasibility**: Zenodo provides direct download links; no credentials required. Fits within CI runner constraints.
- **License**: Open Access (CC-BY).

### Secondary Datasets (Verified Sources Only)
The following verified datasets from the `# Verified datasets` block are available but **NOT** used for the primary analysis to ensure consistency with the Zenodo experimental barriers:
- **HOMO**: ` (Available but not selected for this study; Zenodo source preferred for barrier correlation).
- **DFT**: ` (Available but not selected; we compute DFT descriptors ourselves for the subset).
- **SMILES**: ` (Available but not selected; Zenodo source is the ground truth).

**Decision**: The Zenodo dataset is the single source of truth for experimental barriers. We do not use external HOMO/LUMO datasets because the study requires *computed* descriptors from the *same* molecules to ensure valid comparison.

### Data Availability & Streaming
- The Zenodo dataset is expected to be small (<100MB) for SMILES and barriers, allowing full download.
- If the dataset exceeds memory, we will stream using `pandas.read_csv(..., chunksize=...)` or `datasets.load_dataset(..., streaming=True)` if a HF mirror exists (not currently verified).
- **No access-gated data**: Zenodo is open access.

## Methodology

### 1. Geometry Optimization (DFTB+)
- **Tool**: `dftb+` (Semi-empirical).
- **Input**: SMILES → 3D coordinates (RDKit) → DFTB+ optimization.
- **Strategy**:
 - Generate initial 3D conformation using RDKit.
 - Run DFTB+ geometry optimization.
 - **Retry Logic**: If convergence fails, retry **once** with a different initial guess (randomized perturbation).
 - **Failure Handling**: If retry fails, log to `logs/convergence_failures.log` with `molecule_id`, `timestamp`, `error_code`, `error_message`.
- **Resource Fit**: DFTB+ is CPU-efficient and fits within 2-core/7GB RAM constraints.

### 2. Descriptor Calculation
- **Semi-Empirical (DFTB+)**:
 - Compute HOMO, LUMO, Mayer bond orders from optimized geometries.
 - **Note on Mayer Bond Order**: While Mayer bond orders are a matrix, we use the sum of bond orders as a proxy for molecular size/bonding capacity, acknowledging this loses specific bond information (Scientific Soundness limitation).
 - Output: `data/descriptors_semi.csv`.
- **High-Level (Psi4)**:
 - **Subset**: Stratified random sample of 50 molecules (stratified by **barrier height bins**). If N < 50, use all N.
 - **Input**: Use the *exact same* optimized geometries from DFTB+ (Constitution Principle VI).
 - **Method**: DFT (e.g., B3LYP/6-31G*) for consistency.
 - **Output**: `data/descriptors_dft.csv`.
- **Confounds (FR-008)**:
 - Compute Molecular Weight (MW), atom count, and functional group enumeration using RDKit (`rdkit.Chem.Lipinski`, `rdkit.Chem.Descriptors`).
 - Output: `data/confounds.csv`.

### 3. Modeling & Evaluation
- **Models**: Two Random Forest Regressors (Scikit-learn).
 - Model A: Trained on `descriptors_semi.csv` (Subset only).
 - Model B: Trained on `descriptors_dft.csv` (Subset only).
 - **Critical**: Both models trained on the **exact same 50 samples** to isolate the method effect.
- **Training**:
 - Fixed train/test splits (same indices for both models).
 - Random seed pinned.
- **Evaluation**:
 - Compute MAE against `experimental_barrier` on the test set.
 - **Paired T-Test**: Compare error distributions (MAE per molecule) of Model A vs. Model B.
 - Null Hypothesis: No difference in error distribution.
 - Significance Level: α=0.05.
 - Output: `reports/evaluation.json` with keys `semi_empirical_mae`, `dft_mae`, `t_statistic`, `p_value`, `null_hypothesis`, `significance_level`.
 - **Success Rate**: Calculate and report the ratio of successfully optimized geometries in `reports/evaluation.json`.

### 4. Sensitivity Analysis (US3)
- **Feature Importance**: Extract from RF models.
- **Stability Check**:
 - Sweep cutoffs: {, 0.05, 0.1}.
 - Inject noise: σ={, 0.05}.
 - Verify rank correlation of top 3 descriptors ≥ 0.9.
 - **Note**: This tests *model* stability to input noise, not physical system stability. Structural uncertainty (geometry errors) is a separate, unquantified source of error.
- **Output**: `reports/sensitivity.csv` with columns `cutoff`, `noise_sigma`, `top_3_descriptors`, `rank_correlation`.

## Statistical Rigor

- **Multiple Comparisons**: Not applicable (only one primary hypothesis test: paired t-test).
- **Sample Size**:
 - Semi-empirical: Subset N=50 (for comparison).
 - DFT: Subset N=50.
 - **Power Limitation**: Acknowledged. N=50 is small for DFT but sufficient for a feasibility study and paired comparison. The study frames DFT results as a high-fidelity baseline, not a population estimate. The t-test may have low power to detect small effect sizes (Type II error risk).
- **Causal Inference**: Associational only. No randomization of molecular properties.
- **Measurement Validity**: HOMO/LUMO/Mayer are standard quantum chemical descriptors. Validation evidence cited from DFTB+ and Psi4 literature.
- **Collinearity**: Acknowledged. HOMO/LUMO often correlated. Feature importance will be reported with correlation matrix inspection.
- **Solvation Limitation**: The experimental barriers may include solvation effects, while calculations are gas-phase. The error metric reflects both method inaccuracy and missing physics.

## Compute Feasibility

- **CPU-First**:
 - DFTB+ optimization: CPU-native, fast.
 - DFT (Psi4) on 50 samples: CPU-native, computationally expensive, limited to subset due to time/memory constraints (Constitution Principle VII).
 - ML (Random Forest): CPU-native, negligible time.
- **GPU Escape Hatch**: Not required. No deep learning or large language models used.
- **Memory**: < 7 GB RAM (DFTB+ and Psi4 are memory-efficient for small molecules; RDKit is lightweight).
- **Disk**: < 14 GB (XYZ files are small; CSVs are small).

## Addressing Unresolved Concerns

- **FR-008 (Confounds)**: `code/confounds.py` will explicitly implement RDKit logic (`rdkit.Chem.Lipinski`, `rdkit.Chem.Descriptors`) to derive MW, atom count, and functional groups from `data/raw/` SMILES. Output `data/confounds.csv` will be generated before US2.
- **T046b (Structural Constraint)**: Removed. The spec defines gas-phase SMILES; no crystallographic data exists. We validate physical validity via `HOMO >= LUMO` checks and retry logic, not external crystal data.
- **T011d/T011e (Ontology/Error Budget)**: Removed. These are philosophical tasks not mapped to FRs. The plan focuses on FR-008 for confounds analysis.
- **Dataset Size (T020)**: The stratified subset logic will check `N` and adjust if `N < 50` (e.g., take all available).
- **Directory Structure (T001a-c)**: The plan explicitly defines the directory tree. The implementation step will create these directories.