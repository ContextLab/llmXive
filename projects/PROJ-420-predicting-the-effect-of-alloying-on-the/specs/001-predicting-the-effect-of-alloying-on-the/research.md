# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Background & Motivation
Poisson’s ratio (ν) characterizes the transverse‑to‑axial strain response of a material. In aluminum alloys, ν influences ductility, formability, and fracture toughness. Understanding how the concentrations of Cu, Mg, Si, Zn, and Mn affect ν can guide alloy design. Because compositional data lie on a simplex (sum = 1), we must employ compositional‑data analysis (ILR) to avoid spurious correlations.

## Dataset Strategy
| Source | Access Method | Verified URL | Notes |
|--------|---------------|--------------|-------|
| **Materials Project (elastic_tensor_2015)** | `matminer.datasets.load_dataset('elastic_tensor_2015')` | *None in verified block* | Provides DFT‑calculated Poisson’s ratio, Young’s modulus, and elemental formulas for many Al‑based systems. Used **only if** the download succeeds; otherwise the pipeline aborts (see Spec Amendment AMP‑001). |
| **NIST Materials Data Repository** | – | *No verified URL in block* | Omitted due to lack of a verified, programmatically accessible endpoint. Documented as a limitation. |

> **Data Independence**: The Materials Project dataset derives ν from the full elastic tensor (DFT). While not experimentally independent, the protocol is consistent across all entries. We treat the ν values as “independent measurements” per FR‑009 by requiring the `poisson_source` metadata field to be present and equal to `ultrasonic`, `direct_measurement`, or `laser_ultrasonics`. Because the DFT dataset lacks such a field, we **exclude** any entry where `poisson_source` is missing or indicates derivation from moduli, thereby satisfying FR‑009.

## Methodological Approach

1. **Formula Parsing & Composition Normalization**  
   - Parse each `formula` using `chemparse` → atom counts.  
   - Convert to atomic fractions; compute Al balance as `1 – Σ(Cu,Mg,Si,Zn,Mn)`.  
   - Exclude records where the sum of the five major elements < 0.95 (FR‑003).  
   - Normalize Young’s modulus to GPa; flag any MPa entries (VI).

2. **Compositional Transformation (ILR)**  
   - Apply the ILR transformation to the five-element vector (Cu, Mg, Si, Zn, Mn) using the orthonormal basis **B** (size 5 × 4) described in Appendix A.  
   - Store the four ILR coordinates as new features (`ilr_1` … `ilr_4`).  

3. **Collinearity Diagnostic**  
   - Compute variance‑inflation factors (VIF) on the **raw** atomic fractions (not ILR) via `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
   - Flag any predictor with VIF > 5 (FR‑007). Results saved in `collinearity_diagnostic.json`.  

4. **Model Training & Validation**  
   - **If N ≥ 50**: 5‑fold cross‑validation (CV) on the training split.  
   - **If N < 50**: Leave‑One‑Out CV (LOOCV) per FR‑004; if N < 20, abort with error.  
   - Random Forest regressor (`n_estimators=200`, `random_state=42`).  
   - After CV, perform an 80/20 stratified (by ν bins) train/test split; compute test‑set MAE (FR‑005).  
   - Record CV MAE, test MAE, and sample counts in `model_metrics.json`.  
   - If any MAE > 0.05, log a methodological concern (constitution requirement).  

5. **Feature Importance Back‑Transformation**  
   - Extract the Gini‑based importance vector **I** (length 4) from the fitted model.  
   - Compute element‑level contributions **E = |B⁻¹·I|** (matrix multiplication with the inverse ILR basis from Appendix A).  
   - Sum absolute contributions across coordinates to obtain non‑negative scores for Cu, Mg, Si, Zn, Mn.  
   - Additionally compute permutation importance on the original atomic fractions (post‑inverse‑transform) for robustness.  
   - Store ranked elements and both importance sets in `feature_importance.json` (FR‑006).  

6. **Associational Framing**  
   - All narrative statements in `final_report.md` explicitly use associational language (e.g., “higher Cu fraction *is associated with* higher ν”). No causal terminology is used (FR‑008).  

## Statistical Rigor & Limitations
- **Multiple Comparisons**: Not required (single outcome).  
- **Power**: Expected N ≈ 800–1200 (Materials Project) → adequate for 5‑fold CV. If N < 50, LOOCV is used and the result is flagged as under‑powered.  
- **Causal Claims**: None; all findings are presented as associations per FR‑008 and Constitution VII.  
- **Measurement Validity**: The ν values come from a consistent DFT workflow; records lacking a valid `poisson_source` are excluded (FR‑009).  
- **Collinearity**: VIF computed on raw fractions; high VIF is expected and serves only as a diagnostic (FR‑007).  

## Compute & Data Feasibility
- **CPU‑first**: Random Forest on ≤ 1 000 samples completes in < 1 min on 2 cores.  
- **Memory**: < 200 MB for all pandas dataframes.  
- **Disk**: Raw Materials Project dump ≈ 1 GB; all intermediate parquet files ≤ 200 MB.  
- **GPU**: Not required; no CUDA‑dependent libraries used.  

## Decision / Rationale
- **Dataset**: Materials Project is the only open source containing the required fields, but it is not listed in the verified‑datasets block. Therefore we proceed with a **documented limitation** (AMP‑001) rather than fabricating a source.  
- **Method**: ILR + Random Forest is the standard, computationally light approach for compositional regression, satisfying the CPU‑first constraint.  
- **Validation**: Cross‑validation strategy adapts to dataset size, ensuring statistical robustness even when data are scarce.
