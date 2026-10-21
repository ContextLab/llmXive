# Research: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

## Problem Definition
Refractive index (RI) is a key optical property for drug formulation and material design. Classical atomic‑contribution methods (e.g., Lorentz‑Lorenz) capture additive effects but often miss subtle electronic interactions such as conjugation or halogen substitution. This study evaluates whether a lightweight Message Passing Neural Network (MPNN) can improve predictive accuracy while remaining feasible on a CPU‑only environment, and whether Integrated Gradients can reveal chemically interpretable drivers of RI.

## Dataset Strategy

### Primary Dataset
- **Name**: *Open Refractive‑Index Dataset* (to be sourced from an open repository such as Zenodo, Figshare, or a public HuggingFace dataset).  
- **Access**: Programmatic download via `code/data/download.py`; checksum recorded for reproducibility.  
- **Variables Verified**:  
  - `smiles` – present, RDKit‑parsable.  
  - `refractive_index` – present, normalized to 20 °C when temperature data is available (Edlén equation applied).  
  - `molecular_weight` – present or computed from SMILES.  

*If no such open dataset is found, the pipeline aborts and the specification is flagged for revision (see Constitution Check).*

### Preprocessing & Filtering
1. **SMILES parsing** via RDKit; invalid entries logged to `logs/failed_parsing.log`.  
2. **Molecular‑weight filter**: exclude molecules with MW > 500 Da (ensures RAM compliance).  
3. **Temperature normalization**: apply Edlén equation when temperature metadata exists; otherwise flag uncertainty.  
4. **Feature engineering**: node features (atomic number, degree, hybridization, aromaticity) and edge features (bond type, conjugation, stereochemistry).  
5. **Global scalar**: normalized molecular weight concatenated to graph readout.

### Data Splitting
- **Method**: Murcko scaffold split (RDKit) with **5 × 5 repeated splits** (5 random scaffold splits, each repeated 5 times) using seeds 100‑104 and per‑repeat seeds.  
- **Ratios**: 80 % train, 10 % validation, 10 % test.  
- **Guarantee**: **Zero scaffold overlap** between train/val/test within each split, mitigating leakage while providing variance estimates across repetitions.

## Methodology

### 1. Baseline: Atomic‑Contribution Model (FR‑004)
- Compute **Molar Refractivity (MR)** using additive atomic fragment constants from public tables (e.g., Meylan et al.).  
- Convert MR → RI via the **Lorentz‑Lorenz** equation.  
- Serves as a physics‑based comparator.

### 2. Graph Neural Network (FR‑002)
- **Architecture**: 3 message‑passing layers, hidden dim = 64, mean aggregation, global average pooling → 2‑layer MLP (64 → 32 → 1) with ReLU.  
- **Training**: MSE loss, Adam optimizer (lr = 1e‑3), early stopping (patience = 10) on validation loss.  
- **Device**: `torch.device("cpu")` enforced per Constitution Principle VI.  
- **Power Note**: Detectable ΔMAE = 0.2 would require ≈ 210 samples for 0.8 power; with ≥ 500 samples we expect sufficient power, but we still report observed power given the actual N.

### 3. Integrated Gradients Attribution (FR‑005)
- **Baseline**: zero‑vector (all‑zero node/edge features).  
- **Steps**: 50 integration steps.  
- **Sensitivity**: also run with mean‑feature and random baselines; report variance of top‑10 scores.  
- **Output**: `results/attributions_{i}_{j}.csv` containing a `top_features` array per molecule (conforms to the `FeatureAttribution` entity).

### 4. Evaluation & Statistical Rigor (FR‑006)
- **Metrics**: MAE, RMSE for GNN and baseline on each test split.  
- **Paired error differences**: computed per molecule.  
- **Statistical test**: Perform a **paired t‑test** on the error differences.  
  - Assess normality with Shapiro‑Wilk; if violated, fall back to a **Wilcoxon signed‑rank test**.  
- **Effect size**: Report **Cohen’s d**, 95 % confidence interval, and the p‑value (with explicit power disclaimer).  
- Summarize across the 25 splits in `results/metrics_summary.csv`.

### 5. Plot Generation (FR‑007)
- **Parity plot** (Predicted vs. Actual) → `parity_{i}_{j}.png`.  
- **Feature‑importance bar chart** (average attribution per feature type) → `importance_{i}_{j}.png`.  
- PNG files compressed < 5 MB.  
- Aggregate plots across splits into `results/plots/average_parity.png` and `average_importance.png`.

### 6. Robustness & Sensitivity (User Story 3)
- **Variance reporting**: compute variance of test MAE across the 25 splits; report observed value (target < 0.01 noted as aspirational).  
- **Hyper‑parameter sweep** on L2 weight decay ∈ {0, 1e‑4, 1e‑3}; MAE vs. decay plotted in `results/robustness/l2_sweep.png`.  
- Results are interpreted with explicit caveats about dataset size.

### 7. Contract Validation
- **Dataset** validated against `contracts/dataset.schema.yaml`.  
- **Outputs** validated against `contracts/output.schema.yaml`.  
- Validation failures abort the pipeline with a logged error.

## Compute Feasibility
- **CPU‑First**: No CUDA imports; PyTorch Geometric built for CPU.  
- **Memory**: Dataset < 10 MB; peak RAM < 1 GB.  
- **Time**: End‑to‑end runtime on GitHub Actions free tier estimated ≤ 5 h for all 25 splits, within the 6 h limit.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open RI dataset ≥ 500 samples | Fatal to FR‑001 | Abort with clear message; request specification revision. |
| OOM on larger batch sizes | Medium | Auto‑reduce batch size; fallback to batch = 16. |
| Overfitting on limited data | High | Early stopping, dropout 0.2, L2 = 1e‑4; report pilot nature, no strong claim. |
| Attribution baseline bias | Medium | Sensitivity analysis across multiple baselines. |
| Low statistical power | Medium | Use paired test with explicit power disclaimer; also report effect sizes and CI. |

---
