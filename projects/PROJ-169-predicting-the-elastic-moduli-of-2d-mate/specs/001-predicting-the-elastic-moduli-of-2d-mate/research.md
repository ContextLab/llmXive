# Research: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Problem Definition
Predict Young’s modulus, shear modulus, and Poisson’s ratio of 2D crystalline materials using a **structure‑only surrogate** (graph‑based GNN). The surrogate learns statistical relationships from pre‑computed DFT elastic tensors; it does **not** solve the Schrödinger equation. All conclusions are strictly associational and limited to the chemical space represented in the training data.

## 2. Dataset Strategy
Only verified, programmatically downloadable parquet files that contain **2‑D crystal structures with complete 6‑component elastic tensors** may be used. **At present no open, verified source with the required columns exists**; the pipeline will abort with a clear error if such a dataset cannot be fetched. Potential open sources (to be verified by the implementer) include:

| Dataset | Verified URL | Content | Role |
|---|---|---|---|
| Materials Project 2D Elastic Tensor Collection | *None (no verified open URL currently available)* | DFT‑computed 2D structures + full elastic tensors, CIFs, `is_2d` flag | Canonical source (if verified) |
| C2DB 2D Elastic Dataset (Zenodo) | *None (no verified open URL currently available)* | Same schema, alternative source | Backup |
| Open Materials Database 2D Elastic (Figshare) | *None (no verified open URL currently available)* | Same schema, second backup | Backup |

**Dataset‑variable fit**: The loader validates that each row contains (i) a CIF/structure representation, (ii) a 6‑component Voigt elastic tensor, (iii) space‑group number, and (iv) an `is_2d` boolean flag. If any required column is missing, the pipeline aborts with a clear error; no synthetic data are generated.

## 3. Methodology

### 3.1 Graph Construction
- **Node features**: atomic number, electronegativity, covalent radius, group, period.  
- **Edge definition**: PBC‑aware neighbor list using a cutoff `r_A + r_B + 0.5 Å`.  
- **Edge features**: Euclidean distance, electronegativity difference.  

All graphs are stored in `data/processed/graphs_v1.parquet` (see `contracts/dataset_schema.schema.yaml`).

### 3.2 Model Architecture
- **Lightweight Message‑Passing Neural Network** (MPNN) with 2 message‑passing layers, hidden dimension ≤ 64, ReLU activation, global mean pooling.  
- **Loss**: weighted normalized MSE on the three targets (targets z‑scored; Poisson’s ratio weighted to balance units).  
- **Training**: Adam optimizer, learning rate 0.001, early stopping on validation loss, batch size 16.  
- **Device**: forced CPU (`torch.device("cpu")`); asserts `torch.cuda.is_available() == False`.

### 3.3 Train/Validation/Test Split
- **Family definition**: `family = space_group + "_" + stoichiometry_class` (e.g., “187_MoS2”).  
- **Clustering**: `StructureMatcher` groups structures with identical space group and stoichiometry.  
- **Split**: train/validation/test (70/15/15 %) with seed = 42. No family appears in more than one split (leakage check in `splitter.py`).

### 3.4 Baseline Comparisons
1. **Composition‑only baseline**: Linear regression on Magpie compositional descriptors (35 features).  
2. **Composition‑only GNN control**: Same lightweight MPNN architecture but restricted to composition‑derived node features and no edge features (Task T018c).  
3. **Metric**: Relative Mean Absolute Percentage Error (MAPE) reduction = `(baseline_mape - surrogate_mape) / baseline_mape`.  
4. **Success thresholds**: ≥ 10 % reduction **and** paired‑bootstrap p < 0.05 (SC‑002).  

### 3.5 Power Analysis & Sample‑Size Justification
- Conduct a paired‑bootstrap power simulation with **1 000 simulation runs** to estimate the probability of detecting a 10 % MAPE reduction at α = 0.05 given the actual test‑set size (≥ 150 samples).  
- Power is deemed sufficient when ≥ 80 % (SC‑006).  
- If the estimated power falls below 0.8, the pipeline aborts and reports the shortfall.

### 3.6 Feature Importance & Ablation
- **Integrated Gradients (Captum)**: Computes node‑ and edge‑level attributions for the surrogate GNN (**100 Monte‑Carlo samples**).  
- **SHAP (KernelExplainer)**: Applied to a random **200‑sample subset**; reports mean absolute SHAP magnitude per descriptor.  
- **Multicollinearity control**: Variance Inflation Factor (VIF) computed for all structural descriptors; descriptors with VIF > 5 are **removed** before importance ranking.  
- **Combined report**: Descriptors must (a) survive VIF screening, (b) rank in the top‑3 by Integrated Gradients magnitude **and** by SHAP magnitude. At least three such descriptors are required (SC‑005).  

### 3.7 Statistical Rigor
| Aspect | Treatment |
|---|---|
| Multiple comparisons | Holm‑Bonferroni correction applied to the three target‑property tests. |
| Power / Sample size | Power analysis described in §3.5; **1 000 bootstrap resamples** for CI; **1 000 paired‑bootstrap resamples** for hypothesis test on MAPE reduction. |
| Causal framing | All statements explicitly labeled *associational*; surrogate interpolation of DFT data only. |
| Measurement validity | Ground‑truth elastic tensors taken directly from the verified parquet files (if available). |
| Predictor collinearity | VIF screening mitigates collinearity; Integrated Gradients and SHAP together reduce bias. |

## 4. Compute Feasibility
- **CPU‑first**: All steps run on a limited number of CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑time.  
- **Memory management**: Streaming parquet load (`datasets.load_dataset(..., streaming=True)`) for ingestion; `tracemalloc` monitors training memory.  
- **Inference speed**: Expected < 50 ms per graph on the runner (well under the 100 ms SC‑003 limit).  
- **No GPU escape hatch**: Model size and batch configuration are chosen to be fully tractable on CPU; therefore no GPU fallback is required.

## 5. Decision Rationale
| Decision | Reason |
|---|---|
| Use only verified open parquet files (if any) | Guarantees unattended download on CI; avoids gated datasets. |
| Lightweight MPNN with ≤ 64 hidden units | Fits within 7 GB RAM and < 6 h runtime on free tier. |
| Family‑based split | Enforces the “unseen chemical families” requirement (SC‑002) and prevents memorization. |
| Integrated Gradients + SHAP + VIF | Provides graph‑appropriate, multicollinearity‑aware importance scores, satisfying SC‑005 and methodological soundness. |
| Baseline GNN (composition‑only) | Isolates the contribution of structural descriptors beyond composition (addresses FR‑005 and methodology‑3ac8e575). |
| Power analysis gate | Guarantees that the study is not under‑powered to detect the targeted improvement (addresses methodology‑946c7f4c). |
| Hard gates with exit codes | Guarantees that any violation (memory, inference time, title audit, power, statistical significance) stops the pipeline, preventing silent fabrication. |
| Disclaimer template (`disclaimer_template.py`) | Centralizes the required scientific‑integrity statement for reuse across scripts (FR‑006, T046). |

---



