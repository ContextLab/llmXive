# Research: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Research Question
*Can a machine learning model trained **exclusively** on 2‑D topological descriptors (derived from SMILES) predict the scalar dipole moment magnitude (`Dipole_debye`) of QM9 molecules with sufficient accuracy for lightweight screening, and which 2‑D descriptors carry the strongest predictive signal?*

## Dataset Strategy

| Role | Source | Loader | Verified URL | Variables |
|------|--------|--------|--------------|-----------|
| Primary | QM9 (open quantum‑chemical benchmark) | `qm9pack.get_data('qm9')` | ` | **Predictors**: SMILES → 2‑D descriptors (≥200). **Outcome**: `Dipole_debye` (scalar dipole in Debye). No additional covariates. |

- **Variable Fit**: The dataset provides both SMILES strings and the target dipole magnitude (`Dipole_debye`). All required predictors are derived from SMILES; no external variables are needed.  
- **Feasibility**: On the order of one hundred thousand rows fit comfortably in the 6 GB RAM budget when processed in streaming/chunked mode.  

### Excluded Datasets
- Any dataset that only supplies TPSA, SMARTS counts, or lacks dipole moments is excluded per FR‑001.

## Methodological Rigor

### 1. Feature Engineering (2‑D Only)
- **Tools**: `rdkit.Chem.Descriptors`, `rdkit.Chem.rdMolDescriptors`.  
- **Exclusions**: No calls to `AllChem.EmbedMolecule`, `Get3DConformer`; TPSA, TPSA_E, and SMARTS‑based functional‑group counts are omitted.  
- **Descriptor Count**: ≥ 200 distinct 2‑D topological descriptors (connectivity indices, atom counts, ring counts, etc.).  

### 2. Collinearity Mitigation
- **VIF Calculation**: Iteratively remove the descriptor with the highest VIF > 5.0.  
- **Fallback**: If removal would leave **fewer than 150** descriptors, the pipeline switches to an L1‑regularized LightGBM model (instead of further pruning), preserving the ≥ 150 descriptor requirement (FR‑007).  

### 3. Model Training
- **Algorithm**: LightGBM Gradient Boosting Regressor (CPU‑optimized).  
- **Data Split**: Random train/test split (no stratification).  
- **Cross‑Validation**: k‑fold (k = 5, deferred) for hyper‑parameter tuning; seeds logged for reproducibility.  
- **Baseline**: Null model predicting the training‑set mean dipole.  

### 4. Evaluation & Interpretability
- **Metrics**: R², RMSE; comparison against null baseline (SC‑001).  
- **SHAP**: Compute SHAP interaction values to accommodate correlated descriptors; generate summary plot.  
- **Bootstrap Stability**: 100 bootstrap resamples of the full dataset; each resample trains on a 10 k subsample (CPU‑friendly). Compute Jaccard similarity of the top‑10 SHAP features across resamples (target ≥ 0.7, SC‑003).  
- **Single‑Feature Validation**: Train ten LightGBM models each using only one of the top‑10 SHAP features; record per‑feature R² (must be ≥ 0.02, SC‑009).  

### 5. Statistical Considerations
- **Multiple Comparisons**: The bootstrap Jaccard assessment serves as a family‑wise error control for feature‑selection stability.  
- **Power**: Full QM9 (≈ 130 k) provides ample power; subsampling for bootstraps is a computational compromise, not a statistical limitation.  
- **Observational Framing**: Claims are limited to predictive association; no causal inference is asserted.  

### 6. Edge‑Case Handling
- **Malformed SMILES**: Logged and skipped; pipeline continues.  
- **Undefined Stereochemistry**: Normalized to the most common stereoisomer; proportion logged (must be ≤ 5 %).  
- **Highly Flexible Molecules**: Identified via rotatable‑bond count ≥ 5; flagged as outliers; dual heuristics (rotatable‑bond count and a simple torsional‑flexibility score) used; Jaccard ≥ 0.8 required for reproducibility (SC‑007).  
- **NaN Descriptors**: Median imputation; records with > 5 % missing descriptors are dropped, with a log entry (SC‑010).  

## Compute Feasibility
- **CPU‑First**: All libraries (RDKit, LightGBM, SHAP) run efficiently on the GitHub Actions free tier.  
- **Memory Management**: Streaming read of the QM9 Parquet file; descriptor generation in batches of 5 k molecules keeps peak RAM < 6 GB.  
- **Runtime Estimate**:  
  - Data download & preprocessing: ~1.5 h  
  - VIF pruning & clustering: ~0.5 h  
  - LightGBM training (CV): ~1 h  
  - SHAP + bootstrap (100 × 10 k) : ~2.5 h  
  - Total < 6 h, satisfying Principle VII.  

## Decision / Rationale
- **LightGBM** selected for speed, CPU efficiency, and native feature‑importance support.  
- **QM9** is the only openly accessible dataset providing high‑quality dipole magnitudes matched to SMILES, satisfying the data‑availability requirement.  
- **VIF + L1 fallback** ensures compliance with FR‑007 while preserving enough descriptors for meaningful SHAP analysis.  
- **3‑D Baseline (FR‑010/011)** omitted due to direct conflict with Constitution Principle VI; therefore **SC‑008** (ΔR²) cannot be computed under the current constitution. The specification must be amended if a 3‑D comparison is desired.  

---


