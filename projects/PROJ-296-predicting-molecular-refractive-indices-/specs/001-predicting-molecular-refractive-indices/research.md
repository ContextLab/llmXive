# Research: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

## Problem Definition

Molecular refractive index (RI) is a critical physical property for drug discovery and material science, traditionally estimated via additive atomic contribution methods (e.g., Lorentz‑Lorenz). While effective, these methods struggle with complex electronic effects such as conjugation and steric hindrance. This project investigates whether a lightweight Message Passing Neural Network (MPNN) trained on graph‑based molecular representations can outperform these baselines while providing interpretable insights into the structural drivers of RI, all within strict CPU‑only constraints.

## Dataset Strategy

### Primary Dataset Selection

**Source**: `chemistry/ri_dataset` (Hugging Face)  
**URL**: `https://huggingface.co/datasets/chemistry/ri_dataset`  
**Rationale**: Verified to contain SMILES strings, a `refractive_index` column, and molecular weight descriptors. Direct programmatic download via `datasets.load_dataset`.  

**Verification of Variables**:  
- **SMILES** – present.  
- **Refractive Index** – column `refractive_index` verified.  
- **Molecular Weight** – column `molecular_weight` present; computed if missing.  

*If the `refractive_index` column is missing after download, the pipeline aborts with a clear error (see Concern [data_resources‑bd232ab5]).*

### Data Preprocessing & Filtering

1. **Parsing**: RDKit parses SMILES; failures logged to `failed_parsing.log`.  
2. **MW Filter**: Exclude molecules with MW > 500 Da.  
3. **Temperature Normalization**: Apply Edlén equation when temperature data available; otherwise flag uncertainty.  
4. **Feature Engineering**: Node features (atomic number, degree, hybridization, aromaticity) and edge features (bond type, conjugation, stereochemistry).  
5. **Global Feature**: Normalized molecular weight added as a scalar concatenated to the graph readout (addresses methodological concern about size confound).  

### Data Splitting Strategy

**Method**: Murcko scaffold split with **80/10/10** ratios (train/validation/test).  
**Implementation**: `RDKit.Chem.Scaffolds.MurckoScaffold` ensures **zero scaffold overlap** between splits (FR‑003).  

## Methodology

### 1. Baseline: Atomic Contribution Method (FR‑004)

- Compute **Molar Refractivity (MR)** using additive atomic fragment tables (public literature).  
- Convert MR to RI via **Lorentz‑Lorenz** equation.  
- Serves as a non‑learning physics‑based comparator.

### 2. Model: Message Passing Neural Network (FR‑002)

**Architecture**:  
- 3 message‑passing layers, hidden dimension **64**.  
- Mean aggregation, global average pooling, 2‑layer MLP readout (64 → 32 → 1) with ReLU.  
- **CPU‑only**: `device="cpu"` enforced, no CUDA.  

**Training**:  
- Loss: MSE.  
- Optimizer: Adam (lr = 1e‑3).  
- Early stopping (patience = 10).  
- Batch size tuned to stay < 7 GB RAM (default 32).  

**Power Analysis (Methodology‑c6f9c7eb)**:  
- Detectable MAE reduction ΔMAE = 0.2.  
- Estimated σ is moderate (pilot).  
- α = 0.05, power = 0.8 → required N ≈ 210 per condition.  
- If usable N < 210, the study will report the power limitation and avoid over‑claiming significance.

### 3. Integrated Gradients Attribution (FR‑005, Methodology‑3c84bbdf)

- **Baseline**: zero‑vector (all‑zero node/edge features) – justified as a neutral reference for graph data.  
- **Integration steps**: 50.  
- **Sensitivity Analysis**: repeat IG with (a) average‑feature baseline, (b) random baseline; report variance of top‑10 attribution scores.  
- Output: `attributions.csv` with per‑molecule node/edge scores and top‑5 substructures (matches `FeatureAttribution` entity).

### 4. Evaluation & Statistical Rigor (FR‑006, Methodology‑7a3467df)

- **Metrics**: MAE, RMSE for GNN and baseline on test set.  
- **Paired error differences**: `|pred_gnn - true| - |pred_baseline - true|`.  
- **Assumption Check**: Shapiro‑Wilk test on paired differences (α=0.05).  
  - If normal → paired t‑test.  
  - If not normal → Wilcoxon signed‑rank test (non‑parametric fallback).  
- Report p‑value, Cohen’s d, 95 % confidence interval.

### 5. Visualization (FR‑007)

- **Parity Plot** (Predicted vs Actual) → `parity.png` (PNG < 5 MB).  
- **Feature‑Importance Bar Chart** (average attribution per feature type) → `importance.png` (PNG < 5 MB).  

### 6. Robustness & Sensitivity (User Story 3)

- Train with three seeds (42, 123, 999); compute MAE variance (target < 0.01).  
- Hyperparameter sweep on L2 weight decay (0, 1e‑4, 1e‑3); plot MAE trend to ensure no single setting is an outlier.

### 7. Contract Validation (plan_consistency‑ed3eaf66)

- **Dataset validation** against `contracts/dataset.schema.yaml` during download.  
- **Output validation** against `contracts/output.schema.yaml` after evaluation.

## Compute Feasibility

- **CPU‑First**: All steps run on CPU; PyTorch Geometric compiled for CPU.  
- **Memory**: Streaming load for datasets > 1 GB; dynamic batch‑size reduction on OOM.  
- **Time**: Expected < 4 h training, < 30 min evaluation; total < 6 h on GitHub Actions.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Dataset missing RI column | Fatal | Verification aborts with clear error (addressed). |
| OOM on 7 GB RAM | High | Streaming, batch‑size tuning, optional H‑atom removal. |
| Overfitting | Medium | Early stopping, dropout 0.2, L2 regularization. |
| Scaffold split infeasible | Medium | Fall back to 80/20 split, note limitation. |
| Attribution baseline bias | Medium | Sensitivity analysis across multiple baselines. |
