# Research: Predicting Molecular Properties from Topological Data Analysis

## Overview
We evaluate whether topological descriptors derived from shortest‑path distance filtrations add predictive value for **logP** beyond traditional QSPR descriptors. The investigation is strictly associative; we do **not** claim causal inference.

## Dataset Strategy

### Verified Sources
| Dataset | URL | Format | Contains |
|---------|-----|--------|----------|
| PubChem multi‑million canonicalized (subset) | https://huggingface.co/datasets/sagawa/pubchem-10m-canonicalized/resolve/main/data/train-00000-of-00001-e9b227f8c7259c8b.parquet | Parquet (streamable) | `canonical_smiles`, `XLogP3` (used as `logP`) |

### Variable Fit
- **Required columns**: `canonical_smiles` (renamed to `smiles`) and `XLogP3` (renamed to `logP`).  
- `01_download_pubchem.py` validates the presence of these columns against `contracts/dataset.schema.yaml`. If either column is missing, the pipeline aborts with a **Data Gap** error.  
- The streaming loader **shuffles** the entire dataset with a fixed random seed (`42`) and then **randomly samples** the first **5 000** valid molecules. This ensures an unbiased sample irrespective of the original ordering.

## Methodological Rigor

### Statistical Framework
1. **Model Comparison**  
   - Feature sets: Traditional, Topological, Combined.  
   - Learners: Linear Regression (L2, α = 1.0) and Random Forest (100 trees, max_depth = 10).  
   - **5 repeats of 10‑fold scaffold‑based cross‑validation** (Bemis‑Murcko, seed = 42) → total **50** paired observations per model configuration.  
   - Metrics per fold: R², RMSE.  

2. **Paired Test**  
   - Perform a **Wilcoxon signed‑rank test** on the **RMSE** differences between the Combined and Traditional models (RMSE is unbounded and more appropriate for a non‑parametric test).  

3. **Multiple‑Comparison Correction**  
   - Apply **Holm–Bonferroni** correction using a family‑wise α = 0.05 (source: https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method) (FR‑005).  

4. **Power Analysis**  
   - For a paired non‑parametric test, a minimum of **N ≥ 30** paired observations is recommended to achieve reasonable power (α = 0.05, power = 0.8, medium effect size).  
   - With **5 repeats of 10‑fold CV**, we obtain **N = 50** RMSE differences, satisfying the power requirement. The script checks that the total number of paired observations meets the N ≥ 30 threshold and aborts with **Power Insufficient** if not.

5. **Collinearity Diagnostics**  
   - Compute Variance Inflation Factor (VIF) for every predictor in the **Linear Regression** model (FR‑007).  
   - Flag predictors with VIF > 5; report in `vif_report.json`.

6. **Redundancy Analysis**  
   - Estimate **Mutual Information (MI)** between the Traditional descriptor matrix and the Topological feature matrix (FR‑009).  
   - Report the MI value to contextualize feature overlap.

7. **Feature Importance Extraction**  
   - After training, extract importance scores for both traditional and topological descriptors (Linear Regression coefficients, Random Forest Gini importance).  
   - Store results in `feature_importance.json` conforming to `model_metrics.schema.yaml`.

8. **Sensitivity Analysis**  
   - Sweep persistence image grid resolutions `{10, 20, 30}` (FR‑006).  
   - Record mean and standard deviation of **R²** for each resolution; **assert that the standard deviation σ < 0.02** to satisfy stability criterion (SC‑002).  

### Assumptions & Limitations
- **Dataset Scope**: Only `logP` is analyzed; solubility and boiling point are omitted due to lack of verified joint sources.  
- **Filtration Choice**: Shortest‑path distance filtration captures graph topology but not 3D geometry.  
- **Causal Claims**: None; findings are associative (Constitution VI).  
- **Computational Limits**: All steps run on CPU; no GPU required (FR‑008).  
- **Data Source**: PubChem dataset is streamed from the Hugging Face repository; no alternative sources are used.  

## References
- **Dataset**: PubChem 10 M canonicalized – Hugging Face repository (verified URL above).  
- **Multiple‑Comparison**: Holm–Bonferroni method, α = 0.05 (source: https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method).  
- **Topological Methods**: GUDHI library documentation (CPU‑only).  

---
