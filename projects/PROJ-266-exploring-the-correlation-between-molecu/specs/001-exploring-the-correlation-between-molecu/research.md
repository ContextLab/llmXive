# Research: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

## Introduction

This research investigates whether molecular flexibility—quantified via normal‑mode‑analysis‑derived torsional variance (dihedral)—correlates with Caco‑2 permeability (logPapp). While lipophilicity (logP) and molecular weight (MW) are established predictors, the dynamic flexibility of drug‑like molecules may provide additional explanatory power for membrane transport efficiency. The primary hypothesis focuses on **dihedral variance** as a proxy for conformational entropy. Bond and angle variances are computed for diagnostic purposes (to detect numerical instability in NMA) but are **excluded** from predictive modeling due to their physical rigidity in organic molecules.

## Methodology

### Data Source Strategy
Primary source: **ChEMBL REST API** (assay_type = Caco-2, standard_type = MEASUREMENT).  
Verified URLs:
- `https://www.ebi.ac.uk/chembl/api/data/assay.json?assay_type=Caco-2&standard_type=MEASUREMENT`

Fallback (only if API fails): Hugging Face dataset `fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors`.

### Computational Workflow

1. **Data Retrieval & Validation (FR‑001, FR‑002, FR‑010)**  
   - Fetch raw JSON, filter for assay_type = Caco-2 and standard_type = MEASUREMENT.  
   - Extract `canonical_smiles`, `logPapp`, `molecular_weight`, `psa`, plus protocol metadata (`lab_id`, `temperature`, `passage_number`).  
   - Remove records with NULL SMILES or NULL logPapp; report pass rate (target ≥ 83%).  
   - Log excluded records due to protocol heterogeneity.

2. **Conformer Generation (FR‑003) with Convergence Validation**  
   - Use RDKit `EmbedMultipleConfs` (initial batch = 50 conformers, energy window ≤ 10 kcal/mol).  
   - **Iterative Convergence Loop**:  
     - Calculate torsional variance for the current ensemble.  
     - Increase conformer count (50 → 75 → 100) and recalculate.  
     - **Convergence Criterion**: The relative change in torsional variance between iterations must be < 1%.  
     - If convergence is not achieved at 100 conformers, the molecule is flagged as "under-sampled" and excluded from primary analysis to prevent bias.  
   - Batch size = 100 to keep RAM < 5 GB.

3. **Normal‑Mode Analysis (NMA) – PyVib (Constitution VI)**  
   - For the lowest‑energy conformer of each molecule (from the converged ensemble), run `pyvib` to obtain vibrational frequencies (Hessian matrix).  
   - **Derivation of Torsional Variance**:  
     - Extract eigenvalues (λ) corresponding to dihedral modes.  
     - Convert to force constants: `k_eff = λ`.  
     - Apply equipartition theorem: `<θ^2> = k_B * T / k_eff` (where T = 300K).  
     - Resulting unit: rad².  
   - **Bond/Angle Metrics**: Compute bond and angle variances similarly but mark them as `diagnostic_only`. They are **not** used as predictors in the regression model.

4. **Flexibility Descriptor Calculation (FR‑004)**  
   - Compute **dihedral_variance** (primary predictor) in rad².  
   - Compute **size_normalized_flexibility** = `dihedral_variance / num_rotatable_bonds` to decouple size from flexibility.  
   - Record `conformer_count`, `nma_success`, and `convergence_flag`.  
   - Bond/angle variances are stored for QA but excluded from downstream modeling.

5. **Statistical Analysis (FR‑005, FR‑006, FR‑009)**  
 - **Power Analysis**: Prior to testing, compute detectable effect size (MDES) for expected N. If N < 150 or MDES > 0.3, log "Limited Power" warning but proceed.
   - **Correlation**: Pearson & Spearman between `dihedral_variance` and logPapp; compute p‑values.  
   - **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR (q < 0.05).  
   - **Robustness**: Test normality of logPapp (Shapiro-Wilk). If p < 0.05, apply Box‑Cox transformation. Use **HuberRegressor** by default to handle heteroscedasticity and outliers.  
   - **Collinearity**: Calculate VIF for all predictors. If any VIF > 5, switch to **Ridge Regression** (α = 1.0).

6. **Multivariate Modeling (FR‑007)**  
   - Model: `logPapp ~ dihedral_variance + size_normalized_flexibility + logP + MW + PSA + protocol_covariates`.  
   - Protocol covariates (lab_id, temperature, passage) are one‑hot encoded.  
   - 5‑fold cross‑validation; report mean R², RMSE, MAE, fold‑specific scores.

7. **Visualization (FR‑008)**  
   - Scatter plot of **dihedral_variance** vs. logPapp (Box-Cox transformed if applicable) with regression line, 95% CI, and confidence bands.  
   - Export PNG @ dpi.

8. **Citation Validation (Constitution II)**  
   - Run `code/validate_citations.py` after data fetch; enforce title‑overlap ≥ 0.7.

9. **Checksum Recording (Constitution III & V)**  
   - `code/utils/checksum.py` computes SHA‑256 for every file in `data/` and writes entries into the `artifact_hashes` map in `state/projects/PROJ-266...yaml`.

### Protocol Heterogeneity Control
- Protocol fields (`lab_id`, `temperature`, `passage_number`) are one‑hot encoded and added as covariates.  
- Optional stratified 5‑fold CV by `lab_id` to assess robustness across labs.

### Power Analysis & Stopping Rule
- Using `statsmodels.stats.power.FTestPower`, we target detectable effect size **r = 0.20** (≈ f² = 0.04).  
- If after filtering the valid sample size **N < 150**, the pipeline logs "Insufficient power" and proceeds with a "Limited Power" flag rather than aborting.

## Results (to be generated)

- **Dataset Completeness**: pass rate (valid / raw).  
- **Conformer/NMA Success**: success rate (valid / attempted) and convergence rate.  
- **Correlation**: Pearson/Spearman r, p‑value, FDR‑corrected q for dihedral variance only.  
- **Model Performance**: mean R², RMSE, MAE, VIF values, collinearity handling notes.  
- **Visualization**: `plot.png` path.

## Discussion

- **Interpretation**: Will discuss strength/direction of flexibility–permeability link, focusing on dihedral variance.  
- **Limitations**:  
  - Observational design → associational only (FR‑009).  
  - Power limitation if N < 150.  
  - Potential residual collinearity despite VIF mitigation.  
  - Protocol heterogeneity may still bias if unmeasured factors exist.  
  - Bond/angle metrics excluded due to physical rigidity (noise-dominated).  
- **Future Work**: Experimental validation, larger open datasets, exploration of alternative flexibility metrics.

## Decision/Rationale

- **Why ChEMBL?** Open, programmatic, contains required SMILES and logPapp.  
- **Why PyVib?** Satisfies Constitution Principle VI (normal‑mode analysis) and provides physically meaningful torsional variance via Hessian eigenvalues.  
- **Why CPU‑Only?** All steps fit within GitHub Actions limits; eliminates reproducibility risk from optional GPU offload.  
- **Why Robust Methods?** Address heteroscedasticity and collinearity per methodological concerns.  
- **Why Protocol Covariates?** Directly control for assay‑level heterogeneity identified as a hidden confound.  
- **Why Exclude Bond/Angle?** They are physically rigid in organic molecules; including them dilutes the signal of conformational entropy.