# Research: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Problem Definition

The goal is to predict elastic moduli (Young's, Shear, Poisson's ratio) for 2D materials using a **Structure-Only Surrogate Model**. This is a machine learning interpolation task, not a first-principles calculation. The model learns the mapping from crystal structure (graph representation) to elastic properties based on pre-computed DFT data.

**Critical Distinction**: The model does *not* solve the Schrödinger equation. It approximates the statistical correlation between structural descriptors and DFT-derived properties. Claims of "discovering new physics" are strictly forbidden; insights are limited to identifying structural determinants within the training distribution. The ground truth is **DFT-derived**, not experimental.

## 2. Dataset Strategy

The project relies on **verified, open, programmatic datasets** from HuggingFace. No access-gated data is used.

### Verified Datasets

| Dataset Name | Source URL | Content | Suitability |
| :--- | :--- | :--- | :--- |
| **MatBench Elasticity** | `https://huggingface.co/datasets/matbench/elasticity` | Training/Testing splits of DFT elastic tensors. | **Primary Source**. Contains `elastic_tensor` (6 components) and `structure` (CIF) fields. Verified schema match. |

**Dataset Selection Rationale**:
- **Availability**: Direct programmatic access via `datasets.load_dataset`. No registration required.
- **Completeness**: Verified to contain `elastic_tensor` and `structure` fields required for graph construction.
- **Fit**: Contains exact predictors (structure) and outcomes (elastic moduli).
- **Feasibility**: Streamed or sampled to fit 7GB RAM.

**Data Handling Strategy**:
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)`. If metadata index exceeds 7GB, fallback to a random sample of [deferred] rows (log power limitation).
- **Checksumming**: Every downloaded file is checksummed (SHA-256) and recorded in `state/...yaml`.
- **Schema Validation**: T013d1 validates the presence of `elastic_tensor` and `structure` before processing.

## 3. Methodology

### 3.1 Graph Construction
- **Nodes**: Atoms. Features: Atomic number, electronegativity, covalent radius.
- **Edges**: Bonds. **PBC-Aware**: Uses `pymatgen` to create edges across unit cell boundaries.
- **Threshold**: Adaptive cutoff: `covalent_radius_A + covalent_radius_B + 0.5 Å`. This avoids fixed cutoff artifacts for materials with varying bond lengths.

### 3.2 Model Architecture
- **Type**: Graph Neural Network (GNN), specifically a Message Passing Neural Network (MPNN).
- **Constraints**: Lightweight (2-3 layers, hidden dim <= 64) to fit 7GB RAM.
- **Loss Function**: **Weighted/Normalized MSE**.
  - Young's and Shear moduli are normalized by dataset mean/std.
  - Poisson's ratio is weighted to ensure equal contribution.
  - Prevents GPa-scale targets from dominating the gradient.

### 3.3 Training & Validation
- **Split Strategy**: **Inter-Family Stratified Split**.
  - **Family Definition**: A composite key of **Space Group** + **Dominant Anion/Cation Motif** (e.g., "TMD" = Space Group 187 + "S" anion).
  - **Rationale**: Prevents leakage where structural motifs overlap between families.
- **Metric**: Primary: **RMSE** (stable for wide ranges). Secondary: **MAPE** (for interpretability).
- **Power Analysis**: With [deferred] entries, test set may be small (<50). Pipeline computes 95% CI for MAPE.
  - **Gate Logic**: Fail if RMSE > threshold OR (MAPE > 15% AND Lower CI Bound > 15%).
- **Hard Gate**: If criteria not met, pipeline exits with code 1.

### 3.4 Statistical Rigor
- **Multiple Comparisons**: Not applicable for primary regression.
- **Power Limitation**: Acknowledged if test set < 50. Reported in `generalization_metrics.json`.
- **Collinearity**: Structural descriptors (bond length vs. coordination) are correlated.
  - **Method**: **SHAP (Shapley Additive Explanations)** with interaction values.
  - **Rationale**: Better handles correlated features than permutation importance.
- **Causal Claims**: None. All claims are associational: "Structure X correlates with Property Y within the DFT training distribution."
- **Limitations**: Structural descriptors are derived from the same structure as the outcome. SHAP values represent "correlation importance", not causation.

## 4. Compute Feasibility

- **CPU-First**: Entire pipeline designed for 2 CPU cores, 7GB RAM.
- **Memory Management**:
  - Graph construction: Batch processing.
  - Training: Small batch sizes (16-32).
  - Model: Hidden dim <= 64.
- **No GPU**: Plan avoids GPU-only methods.

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **GNN over RF/XGBoost** | GNNs capture spatial relationships in crystal structures better than tabular models. |
| **Inter-Family Split (Composite Key)** | Prevents leakage; tests true generalization to unseen topologies. |
| **SHAP over Permutation** | Handles collinearity in structural descriptors. |
| **RMSE + MAPE** | RMSE is stable for wide ranges; MAPE is interpretable. |
| **PBC-Aware Graph Builder** | Essential for correct connectivity in 2D materials. |
| **Adaptive Cutoff** | Avoids artifacts from fixed distance thresholds. |
| **Weighted Loss** | Ensures Poisson's ratio is not dominated by GPa-scale targets. |