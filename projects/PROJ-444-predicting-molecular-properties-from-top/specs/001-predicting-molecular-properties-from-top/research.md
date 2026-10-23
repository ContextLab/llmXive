# Research: Predicting Molecular Properties from Topological Data Analysis

## Overview
This research evaluates whether topological descriptors derived from shortest‑path distance filtrations add predictive value for **logP** beyond traditional QSPR descriptors. The hypothesis is *associational*: TDA features may capture ring‑related topology that overlaps with fingerprint information, and we quantify that overlap.

## Dataset Strategy

### Verified Sources
| Dataset | URL | Format | Contains |
|---------|-----|--------|----------|
| MoleculeNet **Lipophilicity** | *No verified direct download URL available* (must be obtained from the official MoleculeNet repository) | CSV | `smiles`, `logP` (experimental) |

### Variable Fit
- Required columns: `smiles`, `logP`.  
- `01_data_ingestion.py` validates the presence of these columns against `contracts/dataset.schema.yaml` and aborts with **Data Gap** error if missing.  
- No other verified dataset provides both columns; therefore the study is limited to **logP** only (N = 1 hypothesis test).

## Methodological Rigor

### Statistical Framework
1. **Model Comparison**  
   - Three feature sets: Traditional, Topological, Combined.  
   - Two learners: Linear Regression (L2, α = 1.0) and Random Forest (100 trees, max_depth = 10).  
   - 5‑fold scaffold‑based CV (seed = 42).  
   - Metrics per fold: R², RMSE.  
   - Paired **t‑test** (or Wilcoxon signed‑rank if normality fails) on fold‑wise R² differences between Combined vs. Traditional.  

2. **Multiple‑Comparison Correction**  
   - Apply **Bonferroni** correction (Holm–Bonferroni method, α = 0.05) to the p‑value(s) (FR‑005).  
   - Since N = 1, corrected p = raw p × 1, but the procedure is retained for compliance.

3. **Power Analysis**  
   - A priori power analysis (α = 0.05, power = 0.8, effect size d = 0.5) yields **N ≥ 128** required for paired t‑test.  
   - Lipophilicity provides a substantial set of valid molecules; after SMILES validation the pipeline checks `len(valid_molecules) >= 128` and aborts with **Power Insufficient** if not met.

4. **Collinearity Diagnostics**  
   - Compute Variance Inflation Factor (VIF) for every predictor in the **Linear Regression model only** (FR‑007).  
   - Flag predictors with VIF > 5.  

5. **Redundancy Analysis**  
   - Estimate Mutual Information (MI) between the Traditional descriptor matrix and the Topological feature matrix (FR‑009).  
   - Report MI value to contextualize overlap.

6. **Feature Importance Extraction**  
   - After model training, extract and record feature importance scores for both traditional and topological descriptors (FR‑010 removed from spec; kept as reporting).  
   - Output conforms to `model_metrics.schema.yaml` with `feature_importance` object containing separate arrays for traditional and topological importance.

7. **Sensitivity Analysis**  
   - Sweep persistence image grid resolutions `{10, 20, 30}` (FR‑006).  
   - Record R² variance across resolutions; stability criterion is that the standard deviation of R² across resolutions < 0.02 (informal threshold, not a spec constraint).

### Assumptions & Limitations
- **Dataset Scope**: Only logP is analyzed; solubility and boiling point are omitted due to lack of verified joint sources.  
- **Filtration Choice**: Shortest‑path distance filtration is a graph‑only descriptor; does not capture 3D geometry.  
- **Causal Claims**: None; all findings are associative (Constitution VI).  
- **Computational Limits**: All steps run on CPU; no GPU required (FR‑008).  
- **Data Source**: Lipophilicity dataset is obtained from the official MoleculeNet repository; no alternative sources are used.  

## References
- **Dataset**: MoleculeNet Lipophilicity – official MoleculeNet repository (no direct verified URL).  
- **Multiple‑Comparison**: Bonferroni / Holm–Bonferroni method (α = 0.05, source: https://en.wikipedia.org/wiki/Holm–Bonferroni_method).  
- **Topological Methods**: GUDHI library documentation (CPU‑only).  

---

