# Research: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Background & Motivation
Poisson’s ratio (ν) characterizes the transverse‑to‑axial strain response of a material. In aluminum alloys, ν influences ductility, formability, and fracture toughness. Understanding how the concentrations of Cu, Mg, Si, Zn, and Mn affect ν can guide alloy design. Because compositional data lie on a simplex (sum = 1), we must employ compositional‑data analysis (ILR) to avoid spurious correlations.

## Dataset Strategy
| Source | Access Method | Verified URL | Notes |
|--------|---------------|--------------|-------|
| **Materials Project (elastic_tensor_2015)** | `matminer.datasets.load_dataset('elastic_tensor_2015')` | *None in verified block* | Provides DFT‑computed Poisson’s ratio, Young’s modulus, and formulas for many Al‑based systems. Used **only if** the download succeeds; otherwise the pipeline aborts (see Spec Amendment AMP‑001). |
| **NIST Materials Data Repository** | – | *No verified URL in block* | Omitted due to lack of a verified, programmatic endpoint; limitation recorded in the final report. |

> **Data Independence**: The Materials Project dataset derives ν from the full elastic tensor (DFT). To satisfy FR‑009, we require a metadata field `poisson_source` indicating an independent measurement (`ultrasonic`, `direct_measurement`, `laser_ultrasonics`). Entries lacking this field or indicating `derived_from_moduli` are **excluded** during cleaning, and the count of excluded entries is logged. **If no records pass this independence filter, the pipeline aborts with a clear error message** and records the limitation in the final report. This limitation is explicitly noted because no open, verified dataset provides experimentally independent Poisson’s ratio measurements.

## Methodological Approach
1. **Formula Parsing & Composition Normalization**  
   - Parse each `formula` using `chemparse` → atom counts.  
   - Convert to atomic fractions; compute Al balance as `1 – Σ(Cu,Mg,Si,Zn,Mn)`.  
   - Exclude records where the sum of the five major elements < 0.95 (FR‑003).  
   - Normalize Young’s modulus to GPa; flag any MPa entries (VI).  

2. **Compositional Transformation (ILR)**  
   - Apply the ILR transformation to the five‑element vector using the orthonormal basis **B** (5 × 4) from Appendix A.  
   - Store the four ILR coordinates as new features (`ilr_1` … `ilr_4`).  

3. **Collinearity Diagnostic**  
   - Compute variance‑inflation factors (VIF) on the **raw** atomic fractions via `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
   - Flag any predictor with VIF > 5 (FR‑007).  

4. **Train/Test Split (Pre‑CV)**  
   - Perform an 80/20 stratified split (by ν bins) **before** any cross‑validation.  
   - The split ensures that the held‑out test set is never used during model selection or CV, preventing data leakage.  

5. **Model Training & Cross‑Validation**  
   - **If N ≥ 50**: 5‑fold cross‑validation (CV) on the **training** portion only.  
   - **If N < 50**: Leave‑One‑Out CV (LOOCV) per FR‑004; abort if N < 20 with a clear error.  
   - Random Forest regressor (`n_estimators=200`, `random_state=42`).  

6. **Test‑Set Evaluation**  
   - After CV, train the final model on the full training set and evaluate on the held‑out test set.  
   - Compute test‑set MAE; if MAE > 0.05, log a methodological concern (constitution requirement).  

7. **Feature Importance Extraction**  
   - **Primary importance**: Compute permutation importance on the **original compositional features**. For each permutation, the permuted composition is re‑transformed via ILR before being fed to the model, ensuring a valid importance estimate. The resulting element‑level permutation scores are ranked and reported.  
   - **Exploratory back‑transformation**: Extract Gini‑based importance vector **I** (length 4) from the fitted Random Forest, multiply by the inverse ILR basis **B⁻¹** (Appendix A) to obtain element‑level contributions **E = |B⁻¹·I|**, and sum absolute values across coordinates. These scores are reported **only as exploratory insight**, not as the definitive ranking.  

8. **Associational Framing**  
   - All narrative statements in `final_report.md` explicitly use associational language (e.g., “higher Cu fraction *is associated with* higher ν”). No causal terminology is used (FR‑008).  

## Statistical Rigor & Limitations
- **Multiple Comparisons**: Not required (single outcome).  
- **Power**: Expected sample size on the order of a few hundred to over a thousand (Materials Project) → adequate for 5‑fold CV. If N < 50, LOOCV is used and the result is flagged as under‑powered. If N < 20, the pipeline aborts (methodology‑91ab532d).  
- **Causal Claims**: None; all findings are presented as associations per FR‑008 and the constitution.  
- **Measurement Validity**: Independent Poisson’s ratio values are required via `poisson_source`. Since the Materials Project provides DFT‑derived values, the pipeline will abort if no independent measurements are present, and this limitation is documented in the final report (data_resources‑5af3645d).  
- **Collinearity**: VIF computed on raw fractions; high VIF is expected and serves only as a diagnostic (FR‑007).  

## Compute & Data Feasibility
- **CPU‑first**: Random Forest on ≤ 1 000 samples completes in < 1 min on 2 cores.  
- **Memory**: < 200 MB for all pandas dataframes.  
- **Disk**: Raw Materials Project dump ≈ a few GB; all intermediate parquet files ≤ 200 MB.  
- **GPU**: Not required; no CUDA‑dependent libraries used.  

## Decision / Rationale
- **Dataset**: Materials Project is the only open source containing the required fields, but it lacks a verified `poisson_source`. The pipeline therefore includes a strict independence filter and aborts if no qualifying records exist, documenting the limitation rather than fabricating data.  
- **Method**: ILR + Random Forest is the standard, computationally light approach for compositional regression, satisfying the CPU‑first constraint.  
- **Validation**: Cross‑validation strategy adapts to dataset size, ensuring statistical robustness even when data are scarce.  

---


