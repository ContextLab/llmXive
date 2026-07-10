# Research: Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

## 1. Dataset Strategy

The project relies on the **UV-Vis ML** dataset as the primary source for training and evaluation. A secondary check is performed on **PubChem** for SMILES validation, but it lacks $\lambda_{max}$ values and is not used for training.

| Dataset Name | Source URL | Format | Relevance | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **UV-Vis ML** | https://huggingface.co/datasets/introvoyz041/uvvisml/resolve/main/data/uvvisml/data/computed/20210109_computed_df_all.csv | CSV | Contains SMILES and $\lambda_{max}$ values. Primary training source. **Must verify presence of experimental columns.** | **Verified** |
| **PubChem (Canonicalized)** | https://huggingface.co/datasets/sagawa/pubchem-10m-canonicalized/resolve/main/data/train-00000-of-00001-e9b227f8c7259c8b.parquet | Parquet | Used for SMILES validation and scaffold diversity check. **Lacks $\lambda_{max}$**. | **Verified** (No $\lambda_{max}$ guarantee) |
| **SDBS** | *NO verified source found* | *N/A* | Mentioned in spec. **Cannot use URL.** | **Not Verified** |

**Decision**: The implementation will exclusively use the **UV-Vis ML** CSV dataset for training and evaluation. The SDBS dataset is excluded due to lack of a verified source.

**Data Validity Gate (Critical)**:
- **Requirement**: SC-001 and Constitution Principle VI require validation against an *experimental* noise floor.
- **Check**: The ingestion script MUST verify the presence of an `lambda_max_exp` (or similar) column in the CSV.
- **If Present**: Proceed with experimental ground truth.
- **If Absent (Computed Only)**: The plan MUST explicitly reframe SC-001 to "prediction of computed values" and note that the "experimental noise floor" assumption is invalid. The model will learn to replicate the bias of the quantum chemical method, not physical reality.

**Power Analysis & Sampling Strategy**:
- **Statistical Requirement**: SC-005 requires a Wilcoxon signed-rank test with n≥50 samples for adequate power (95% CI).
- **Strategy**: The split logic must ensure the **test set** contains at least 50 molecules.
  - If the total dataset is small, random sampling is avoided; instead, the full dataset is used.
 - If the dataset is large, sampling is performed to ensure the test split ([deferred]) yields n≥50.
  - If the scaffold split results in <50 test samples, the study will explicitly state that statistical significance testing has **low power** and results will be reported as **descriptive** (effect size/delta MAE only).

## 2. Model Architecture & Methodology

### 2.1 Graph Neural Network (GNN)
- **Architecture**: Message Passing Neural Network (MPNN) with 2-3 layers.
- **Parameters**: < 1M (to fit CPU memory and time constraints).
- **Input Features**: Atom type, degree, hybridization, aromaticity, bond type.
- **Output**: Single scalar (predicted $\lambda_{max}$ in nm).
- **Library**: `torch-geometric` (CPU version).
- **Rationale**: MPNNs are state-of-the-art for molecular property prediction and can capture local structural environments relevant to electronic transitions.

### 2.2 Baseline Model
- **Architecture**: ECFP (Extended Connectivity Fingerprint) + **Ridge Regression** (Regularized Linear Regression).
- **Rationale**: ECFPs are high-dimensional and sparse. Without regularization (Ridge/Lasso), a linear model is prone to overfitting on small datasets, creating an unfair baseline. Ridge regression provides a robust, interpretable baseline.
- **Library**: `rdkit` (for fingerprints), `scikit-learn` (for Ridge regression).

### 2.3 Statistical Rigor & Constraints
- **Multiple Comparison Correction**: Not applicable for the primary MAE/R² comparison. Sensitivity analysis (FR-006) will clearly distinguish between primary hypothesis and exploratory sweeps.
- **Sample Size / Power**:
  - **Target**: Test set n ≥ 50.
  - **Low Power Protocol**: If n < 50, the Wilcoxon test is not performed. Results are reported as descriptive (mean delta MAE) with a "Low Power" flag in the output metrics.
- **Causal Inference**: This is an observational prediction task. Claims are framed as **associational**.
- **Measurement Validity**: Dependent on the "Data Validity Gate". If data is computed, the "experimental noise floor" assumption is invalid.
- **Collinearity & Redundancy**:
  - **Baseline**: Pearson correlation (r ≥ 0.9) between ECFP bits will be checked. If found, features are aggregated.
  - **GNN**: Subgraph redundancy (cosine similarity > 0.9) will be detected. Redundant subgraphs will have attribution weights masked (**FR-007**).

## 3. Compute Feasibility Strategy

- **Hardware Target**: GitHub Actions Free Tier (vCPU, 7GB RAM, 6h limit).
- **Memory Management**:
  - Data loading uses `pandas` with `dtype` optimization.
  - Sampling strategy ensures test set n≥50 while fitting in RAM.
  - Batch size in GNN training will be tuned (e.g., 32 or 64).
- **Time Management**:
  - Training epochs limited to 50-100 with early stopping (patience=10).
  - Model size strictly capped at <1M parameters.
  - No GPU/CUDA code paths.
- **Libraries**:
  - `torch`: CPU wheel only (`--index-url https://download.pytorch.org/whl/cpu`).
  - `torch-geometric`: CPU compatible version.
  - `rdkit`: Pre-compiled wheel.

## 4. Risk Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Dataset lacks experimental $\lambda_{max}$** | High: Invalidates SC-001 noise floor assumption. | **Data Validity Gate** detects this; SC-001 is reframed to computed ground truth. |
| **Dataset too large for 7GB RAM** | High: Pipeline crashes. | Implement chunked loading or random sampling ensuring test set n≥50. |
| **Scaffold split yields <50 test samples** | High: Statistical test invalid. | Adjust sampling or report results as descriptive (low power). |
| **GNN fails to converge on CPU** | Medium: No results. | Switch to baseline (ECFP+Ridge) as primary result if GNN fails. |
| **Unregularized Baseline Overfits** | Medium: Unfair comparison. | **Mandatory Ridge/Lasso regularization** for baseline model. |