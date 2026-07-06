# Research: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

## 1. Problem Statement & Hypothesis

**Problem**: Predicting molecular diffusion coefficients in liquids is computationally expensive when using molecular dynamics (MD) simulations.
**Hypothesis**: Static molecular topology (graph structure) combined with scalar solvent descriptors (viscosity, dielectric constant) contains sufficient information to predict diffusion coefficients with a Pearson correlation coefficient (r) > 0.7, outperforming a linear baseline.
**Null Hypothesis**: The graph structure adds no predictive value over simple fingerprints and solvent descriptors (r < 0.3).

**CRITICAL DATA STATUS**: **NO VERIFIED DATASET FOUND.**
As of this writing, no verified dataset URL in the `# Verified datasets` block contains the specific combination of **SMILES + Solvent Properties + Experimental Diffusion Coefficients**.
- **Action**: The project is **PAUSED** for scientific claims.
- **Synthetic Data**: Used **ONLY** for pipeline validation (structural checks, code execution). **NO SCIENTIFIC METRICS (r, RMSE) WILL BE REPORTED** from synthetic runs.
- **Requirement**: The project cannot advance to `research_complete` until a verified dataset is sourced and added to the `# Verified datasets` block.

## 2. Dataset Strategy

The project will utilize a curated dataset of experimental diffusion coefficients. Per the project constraints, **only verified datasets** from the `# Verified datasets` block are used.

**Current Status of Required Data**:
The spec requires a dataset containing:
1. **SMILES** (solute)
2. **Solvent Type** (to map to descriptors)
3. **Experimental Diffusion Coefficient** (target)
4. **Solvent Properties** (Viscosity, Dielectric Constant)

**Verified Sources Analysis**:
- **SMILES Sources**:
 - ` (Contains SMILES, likely no diffusion data).
 - ` (Small sample, likely no diffusion data).
 - ` (SMILES only).
- **NIST/Other Sources**:
 - ` (Medical text, irrelevant).
 - ` (LLM eval logs, irrelevant).
 - ` (LLM eval, irrelevant).

**Gap Identification**:
**CRITICAL**: None of the verified dataset URLs provided in the `# Verified datasets` block contain the specific combination of **SMILES + Solvent Properties + Experimental Diffusion Coefficients**. The available SMILES datasets lack the target variable and solvent context. The NIST/LLM datasets are domain-mismatched.

**Action Plan**:
1. **Do NOT fabricate a dataset**. The plan cannot proceed with a specific dataset URL that does not exist in the verified list.
2. **Data Acquisition Strategy**: The implementation script (`code/featurization.py`) will be designed to accept a CSV/Parquet input file. The `research.md` will explicitly state that the *source* of the data is a placeholder until a verified dataset containing diffusion coefficients is identified and added to the `# Verified datasets` block.
3. **Fallback for Testing (SYNTHETIC ONLY)**: For the purpose of testing the pipeline (CI feasibility), the system will generate a **synthetic** dataset *locally* during the `setup-plan.sh` phase (not committed to `data/raw` as real data) to validate the code structure.
 - **Physics Constraint**: If synthetic data is used, it MUST be generated using a physical proxy (e.g., Stokes-Einstein equation: $D = k_B T / (6 \pi \eta r)$) to ensure the graph structure has a logical relationship to the target. **Random data is insufficient.**
 - **Reporting Constraint**: **NO METRICS (r, RMSE) WILL BE REPORTED** from synthetic runs. The output will only indicate "Pipeline Status: Pass/Fail".
 - **Scientific Block**: The final `research_complete` stage requires a real, verified dataset.

*Note: If a verified dataset for diffusion coefficients is not found, the project scope may need to be adjusted to a different property (e.g., solubility) if a verified dataset exists for it, or the project will be paused pending data acquisition.*

## 3. Methodology

### 3.1 Featurization (FR-001, FR-002)
- **Input**: CSV with `smiles`, `solvent_type`, `diffusion_coefficient`.
- **Molecule Graph**: Use `rdkit.Chem` to parse SMILES.
 - Nodes: Atom type (atomic number), hybridization, formal charge.
 - Edges: Bond type (single, double, aromatic), conjugation.
- **Solvent Descriptors**: Map `solvent_type` to a lookup table of `viscosity` (cP) and `dielectric_constant`.
 - *Handling Missing Data*: If viscosity or dielectric constant is missing for a solvent, the record is excluded and logged `[MISSING_DATA_EXCLUDED]` (FR-007).
- **Output**: JSONL file with `graph` (node/edge features) and `solvent_features` (floats).

### 3.2 Model Architecture (FR-003)
- **GNN**: Message Passing Neural Network (MPNN).
 - Layers: 1-3 layers (sweepable).
 - Aggregation: Sum/Mean.
 - Readout: Global pooling + MLP.
 - **Constraint**: `torch.device("cpu")`. No CUDA.
- **Baseline**: Linear Regression.
 - Features: Morgan Fingerprints (radius 2, 2048 bits) + Solvent Descriptors.

### 3.3 Training & Validation (FR-004)
- **Split**: 5-fold Cross-Validation.
- **Stratification**:
 - **Primary**: By `solvent_type` (to ensure solvent diversity).
 - **Fallback**: If the dataset has too few unique solvents (< 5), switch to **Stratified by Diffusion Coefficient Bin** or **Leave-One-Solvent-Out (LOSO)** cross-validation to ensure statistical independence.
- **Seed**: 42.
- **Optimization**: Adam optimizer, MSE loss.
- **Early Stopping**: Monitor validation loss (patience=5).

### 3.4 Evaluation & Statistics (FR-005, SC-001, SC-002)
- **Metrics**: Pearson Correlation (r), Root Mean Squared Error (RMSE).
- **Significance**:
 1. Perform **Shapiro-Wilk test** on the distribution of absolute errors.
 2. If p > 0.05 (Normal): Use **Paired t-test** on absolute errors of GNN vs. Baseline.
 3. If p < 0.05 (Non-Normal): Use **Wilcoxon signed-rank test** (non-parametric alternative) to ensure validity for small/non-normal datasets.
 4. Hypothesis: GNN error < Baseline error (one-tailed).
- **Ablation**: Retrain GNN *without* solvent descriptors to isolate the contribution of the graph structure. (See Phase 4).
- **Baseline Comparison**: The baseline uses Fingerprints + Solvent. The GNN uses Graph + Solvent. The t-test compares the *performance* of these two distinct representations.

### 3.5 Sensitivity Analysis (FR-006, SC-004)
- **Hyperparameter Sweep**: Message passing steps {1, 2, 3}.
- **Robustness Check**:
 - **PROHIBITED**: Do NOT remove outliers to "confirm stability".
 - **REQUIRED**: Report the correlation *with* all data points included. Analyze the nature of the residuals (e.g., are outliers specific chemical classes?).
 - Report r and RMSE for each hyperparameter setting.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Memory Strategy**:
 - Process molecules in batches.
 - Limit dataset size to [deferred] samples for training (if real data exists).
 - Use `float32` (not `float64`) to reduce memory overhead.
 - **Profiling**: Log `peak_memory_mb` to results JSON (SC-005).
- **Time Strategy**:
 - Limit epochs to 50.
 - If training exceeds 60 minutes, reduce sample size or layers.
 - **Profiling**: Log `total_runtime_seconds` to results JSON (SC-003).
- **No GPU**: All code must explicitly check `torch.cuda.is_available() == False` and raise an error if GPU is detected (to prevent accidental resource waste).

## 5. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **No verified dataset with diffusion coefficients** | **BLOCKING**. Explicitly document the gap in `research.md`. Use synthetic data for pipeline validation only (no metrics). Pause scientific claims until real data is sourced. |
| **Memory Overflow on large molecules** | Implement a filter to exclude molecules with >50 atoms or use a sampling strategy. |
| **Negative Correlation (Null Result)** | Report as a valid scientific finding (r < 0.3). The goal is to test the hypothesis, not force a positive result. |
| **SMILES Parsing Failures** | Robust error handling in `featurization.py` to skip invalid SMILES and log errors. |
| **Fabricated Results** | **STRICT PROHIBITION**. No metrics reported from synthetic data. |

## 6. Decision Log

| Decision | Rationale |
|----------|-----------|
| **CPU-only execution** | Required by CI constraints (no GPU). |
| **Exclusion of missing data** | Imputation introduces bias; exclusion ensures data integrity (Constitution III). |
| **Paired t-test / Wilcoxon** | Required by SC-002 to statistically validate GNN improvement. Fallback to Wilcoxon ensures validity for non-normal distributions. |
| **Synthetic data for CI** | Necessary to validate code structure without a verified real-world dataset yet. **Strictly limited to structural validation (no metrics).** |
| **No outlier removal** | Removing outliers to inflate r is methodologically unsound. Outliers must be reported and analyzed. |