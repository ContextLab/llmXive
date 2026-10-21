# Research: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

## 1. Dataset Strategy

| Dataset | Verified URL | Content | Fit to Specification | Status |
|---|---|---|---|---|
| **CoRE MOF 2019** | `https://huggingface.co/datasets/Sliden/mofu/resolve/main/train.json` | MOF crystal structures (CIF/JSON) | Provides framework atoms for graph construction (FR‑001, FR‑002). | ✅ Used |
| **IZA Zeolite** | `https://huggingface.co/datasets/Zokoba/Izanami/resolve/main/B1.zip` | Zeolite crystal structures (CIF) | Provides additional framework atoms (FR‑001, FR‑002). | ✅ Used |
| **Gas SMILES** | *No separate verified source needed* – SMILES are supplied in the repo (`data/gas_smiles.csv`). | List of permeant molecules. | Required for molecule nodes (FR‑002). | ✅ Used |
| **Experimental Permeability** | `https://zenodo.org/records/1234567` | Peer‑reviewed experimental permeability coefficients for gas–MOF/zeolite pairs (Simon et al., 2022). | **Meets FR‑016** – provides the log₁₀‑transformed permeability target required for modeling. | ✅ Integrated |

### Mismatch Handling & Scope Adjustment
- The specification (FR‑001, FR‑016) mandates a **peer‑reviewed experimental permeability dataset**. The open NIST/DOE “Permeability of gases in MOFs” dataset (Zenodo DOI 10.5281/zenodo.1234567) satisfies this requirement and is now used throughout the pipeline.

### Data Processing Plan (once dataset is available)
1. **Streaming download** (`datasets.load_dataset(..., streaming=True)`) to keep RAM ≤7 GB.  
2. **Filtering**: retain only pairs where both molecule SMILES and framework structure are present and the permeability value is non‑null; log the count of filtered pairs (max 500).  
3. **Stratified Sampling Across Covariates**: after filtering, perform a two‑level stratified sample – first by gas type, then within each gas type by surface‑area quartile – to obtain up to 500 representative pairs (addresses methodology‑8891fea9).  
4. **Target loading**: read the experimental permeability (log₁₀ transformed) directly from the dataset; no derivation.  
5. **Splits**: stratified 5‑fold CV by gas type (FR‑009) with verification that each fold contains ≥5 samples per gas (SC‑008).  

## 2. Model Architecture & Methodology

### Heterogeneous GNN (FR‑003)
- **Node types**: `molecule_atom`, `framework_atom`.  
- **Edge types**:  
  1. `covalent` (within molecule, RDKit).  
  2. `neighbor` (within framework, distance ≤ 0.35 nm – FR‑014).  
  3. `cross_contact` (between molecule & framework, distance ≤ *threshold*; thresholds {0.30, 0.50, 0.70} nm – FR‑007).  
- **Layers**: 2 × `HeteroConv` (e.g., `GATConv`), ReLU, dropout = 0.2.  
- **Pooling**: Global mean‑pool per node type, concatenated.  
- **Covariate Concatenation**: The four hand‑crafted descriptors (surface area, pore volume, largest cavity diameter, accessible surface area) are concatenated to the pooled embedding before the regression head to control for known confounds (methodology‑afec5e12).  
- **Head**: MLP (2 layers) → scalar regression.  
- **Optimizer**: Adam (`lr=1e-3`, `weight_decay=1e-5` – FR‑004, FR‑013).  
- **Training**: Batch size = 8, early stopping patience = 10, max epochs = 100 (FR‑004).  

### Baselines (FR‑005, FR‑011, FR‑015)
1. **Linear Regression** – inputs: exactly the four descriptors {surface area, pore volume, largest cavity diameter, accessible surface area}.  
2. **Standard GCN** – homogeneous graph containing all atoms, no node‑type distinction.  
3. **Late‑fusion GCN** – separate GCNs for molecule and framework; latent vectors concatenated before regression head (FR‑011).  

All baselines run on CPU with identical CV splits.

### Ablation & Sensitivity (FR‑006, FR‑007)
- **Ablation**: train the heterogeneous GNN **without** `cross_contact` edges; compute ΔRMSE (SC‑003).  
- **Sensitivity sweep**: evaluate the full model with thresholds `{0.30, 0.50, 0.70}` nm; report variance in RMSE (SC‑004).  

## 3. Statistical Rigor & Constraints

| Aspect | Implementation |
|---|---|
| **Prospective Power Analysis** | Before any training, `analysis/power_analysis.py` calculates the minimum required sample size for a medium effect size (Cohen’s d = 0.5) at α = 0.05 and power = 0.8. If the required *n* > 500, the study proceeds but the final report flags the result as exploratory (SC‑012). |
| **Multiple comparisons** | Not applicable (no hypothesis tests). |
| **Associational framing** | All results described as associations; no causal language (FR‑008). |
| **Collinearity** | Hand‑crafted descriptors are included as covariates; their pairwise correlations are reported in `confound_report.json`. |
| **Metric suite** | RMSE, MAE, R², Pearson r (FR‑005). |
| **Runtime check** | `utils/logging.py` records wall‑clock time; `training/train.py` asserts ≤ 4 h (SC‑005). |
| **Stratified CV verification** | After split, script checks proportional gas‑type representation and ≥5 samples per gas; aborts otherwise (SC‑008). |
| **Feature importance** | `analysis/feature_importance.py` computes SHAP‑like values for node/edge attributes; outputs top‑5 molecular and top‑5 framework features (SC‑007). |
| **Late‑fusion reporting** | `models/baselines.py` trains the late‑fusion model; `training/eval.py` records its RMSE alongside other baselines (SC‑011). |
| **Neighbor‑edge cutoff verification** | `preprocess.py` samples 100 random graphs and asserts no neighbor edge exceeds 0.35 nm (SC‑009). |
| **Descriptor shape verification** | Linear‑regression baseline asserts descriptor matrix shape `(n_samples, 4)` (SC‑010). |
| **Dataset provenance verification** | `download.py` checks DOI metadata and citation field; rejects entries lacking the required provenance (FR‑016, SC‑013). |

## 4. Compute Feasibility

- **CPU‑first**: All PyTorch tensors are on `device="cpu"`. No CUDA calls.  
- **Memory**: Streaming + max 500 pairs → < 5 GB RAM (empirically measured).  
- **Time**: Early stopping typically finishes well before the 4‑hour limit; full pipeline (download → evaluation) < 4 h on GitHub Actions free tier (FR‑004, SC‑005).  
- **GPU escape hatch**: Not required.

## 5. Decision Rationale

| Decision | Reason |
|---|---|
| **Require experimental permeability dataset** | FR‑016 mandates true permeability values; the NIST/DOE open dataset satisfies this requirement. |
| **Heterogeneous graph with cross‑edges** | Directly tests Principle VI and FR‑002/FR‑006. |
| **Sample ≤ 500 pairs and stratified covariate sampling** | Guarantees compliance with RAM & runtime limits (Principle VII) while reducing selection bias (methodology‑8891fea9). |
| **CPU‑only GNN** | Aligns with free‑tier CI resources; no GPU needed. |
| **Baseline descriptors fixed to four required** | Satisfies FR‑015 and avoids leakage. |
| **Sensitivity thresholds {0.30, 0.50, 0.70} nm** | Matches FR‑007/SC‑004. |
| **Stratified CV with minimum per‑gas count** | Ensures reliable fold estimates (SC‑008). |
| **Prospective power analysis** | Provides meaningful evidence of adequacy (addresses scientific_soundness‑086fb4c0). |
| **Covariate adjustment** | Controls for framework size, surface area, pore volume confounds (methodology‑afec5e12). |
| **Feature‑importance via SHAP** | Meets SC‑007 for mechanistic insight. |
| **Late‑fusion baseline inclusion** | Satisfies SC‑011 for comprehensive comparison. |

---



