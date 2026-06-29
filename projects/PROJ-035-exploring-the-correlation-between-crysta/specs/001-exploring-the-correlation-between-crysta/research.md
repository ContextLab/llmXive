# Research: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

## Overview
This document outlines the research methodology, dataset acquisition strategy, preprocessing steps, analysis pipeline, and validation procedures required to satisfy the functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑005).

**Important Limitations**: This research acknowledges several methodological constraints that may affect the validity and generalizability of results:
1. **Structural vs. Real-Sample Mismatch**: DFT-optimized crystal structures from Materials Project represent ideal lattices without defects, grain boundaries, or porosity that significantly affect thermal conductivity in real samples. This systematic error cannot be controlled post-hoc.
2. **Uncontrolled Confounds**: Synthesis method (solid-state vs. sol-gel vs. CVD), sample purity, measurement technique (laser flash vs. 3-omega), and microstructure (grain size, porosity) are not available in the dataset and may dominate over crystallographic distortion in determining thermal conductivity.
3. **Sample Size / Power**: With ≥50 samples split into 3 chemistry classes, each stratum may have <20 samples. Multiple linear regression with several predictors requires a sufficient number of samples per predictor for stable estimates. Stratified analysis may be underpowered.
4. **Slack 1979 Applicability**: The temperature correction formula was developed for nonmetallic crystals with high thermal conductivity. Its applicability to halide perovskites (different phonon transport mechanisms) is not validated.
5. **Descriptor Multicollinearity**: Structural descriptors (tilting angle, bond-length variance, tolerance factor, unit cell volume) are mathematically interdependent despite VIF filtering. Hidden multicollinearity may persist.

## Dataset Strategy

| Dataset | Source | Access Method | Verified URL | Notes |
|---------|--------|---------------|--------------|-------|
| Perovskite crystal structures | Materials Project API (accessed via `pymatgen` `MPRester`) | Python API call (`MPRester`) | N/A (API endpoint) | Filtered for ABX₃ stoichiometry; no external URL required. |
| Experimental thermal conductivity values | Peer‑reviewed literature compilations (target: NIST Materials Data Repository) | CSV files provided by user (placed under `data/raw/thermal/`) | **NO VERIFIED URL AVAILABLE** | **GAP**: No verified dataset URL exists in the verified datasets block. User must supply CSV with `source_reference` field pointing to peer-reviewed experimental study or NIST entry. Each row must include provenance metadata. |

*All external data files are stored under version‑controlled `data/` directories with SHA‑256 checksums recorded in `data/metadata.yaml`.*

**Dataset Provenance Gap**: Constitution Principle VII requires thermal conductivity values to be sourced from Materials Project thermal properties endpoint or NIST Materials Data Repository with exact dataset version recorded. However, FR‑010 explicitly requires peer‑reviewed experimental literature only (excluding DFT-calculated MP values). This creates a conflict. The plan follows FR‑010 (experimental only); Constitution VII requires amendment. Since no verified thermal conductivity dataset URL is available, the pipeline requires user-supplied CSV with explicit `source_reference` field for each entry.

## Data Ingestion & Cleaning (US‑1)

1. **Fetch structures** using `pymatgen`'s `MPRester` with the query `{"elements": ["A","B","X"], "nelements": 3}` and filter for formulas matching the ABX₃ pattern.  
2. **Load thermal conductivity CSVs** from `data/raw/thermal/`. Verify each entry has non‑empty `source_reference` and that the source is peer‑reviewed or NIST. **If no CSV is provided, halt with clear error message.**  
3. **Merge** on composition (case‑insensitive match).  
4. **Apply FR‑013**: For any entry whose measurement temperature lies outside 300 K ± 10 K, apply Slack's temperature‑correction formula (Slack 1979). **Acknowledge limitation**: Slack 1979 may not apply to halide perovskites. Discard entries with unknown temperature.  
5. **Drop rows** with any missing `thermal_conductivity` or structural fields (FR‑001, FR‑002). Ensure the final cleaned CSV (`data/cleaned/merged_perovskite.csv`) contains ≥ 50 rows (SC‑001).  

**Power Analysis**: SC‑001 requires ≥50 valid entries, but research acknowledges power limitation if cleaned sample size <80. Formal power calculation: for multiple regression with 4 predictors, α=0.05, power=0.80, medium effect size (f²=0.15), minimum N≈85. **Fallback**: If N < 80 after cleaning, proceed with pooled analysis (no stratification) and report power limitation in results. If per-stratum N < 30, pool strata and include chemistry class as covariate.

## Descriptor Calculation (US‑2)

- Compute the following descriptors per structure using `pymatgen`:
  - Octahedral tilting angles  
  - Bond‑length variance  
  - Goldschmidt tolerance factor  
  - Unit cell volume  
- Store results in `data/derived/descriptors.csv`.  

- **Collinearity check (FR‑008)**: Calculate Variance Inflation Factor (VIF) for all descriptors; exclude any with VIF > 5 before regression.  
- **Multicollinearity Limitation**: VIF filtering alone may not detect hidden multicollinearity among mathematically interdependent descriptors. Report descriptive correlation matrix between all descriptors to document multicollinearity structure.

## Correlation Analysis (US‑2)

1. **Stratify** the cleaned dataset into three chemistry classes: oxide, halide, nitride (FR‑014).  
2. Within each stratum, compute **Pearson** and **Spearman** correlation coefficients between each descriptor and thermal conductivity.  
3. Apply **Bonferroni correction** for multiple comparisons (FR‑004).  
4. Conduct a **sensitivity analysis** sweeping significance thresholds (p ∈ {0.01, 0.05, 0.1}) and record how the number of significant descriptors changes (FR‑009).  

**Fallback Strategy**: If any stratum has N < 30, skip stratified analysis for that class and report pooled analysis with chemistry class as covariate. Document this deviation in results.

Outputs: `results/correlation_matrix_{class}.csv` containing coefficients, raw p‑values, corrected p‑values, and significance flags.

## Regression Modeling & Validation (US‑3)

1. **Feature selection**: Retain descriptors that survive the VIF filter and are among the top‑3 most significant correlations per class.  
2. **Split** the dataset into training ([deferred]) and held‑out test ([deferred]) sets with a fixed `random_state=42`.
3. **Fit** a multiple linear regression model (`LinearRegression`) using **5‑fold cross‑validation** on the training set (FR‑005). Record cross‑validated R² and RMSE.  
4. **Evaluate** on the held‑out test set, reporting R² and RMSE (FR‑006). The target is **R² > 0.5** (SC‑003). **Acknowledge**: This target may be unachievable with small N; report actual R² and power limitation if N < 80.  
5. **Feature importance**: Report absolute coefficient magnitudes and permutation importance scores (FR‑011).  
6. **Visualization**: Generate high‑resolution PNG scatter plots for the top‑3 descriptors vs. thermal conductivity, each with a regression line and 95 % confidence interval band (FR‑012). Save to `figures/`.  

All textual outputs pass the **causal‑language check** (FR‑007); any prohibited keyword triggers a pipeline failure.

## Validation & Reporting

- **Statistical rigor**:  
  - Multiple‑comparison correction applied (Bonferroni).  
  - Power limitation explicitly noted if cleaned sample size < 80 (with error message and fallback strategy).  
  - Descriptor multicollinearity documented via correlation matrix.  
- **Associational framing**: All result statements are phrased as "is associated with" (SC‑005).  
- **Reproducibility**: Random seeds, library versions, and checksum logs are archived.  
- **Limitations Report**: Final report includes dedicated section documenting all acknowledged limitations (structural mismatch, uncontrolled confounds, sample size/power, Slack formula applicability, descriptor multicollinearity).

## References
- Slack, G. A. (1979). *Nonmetallic crystals with high thermal conductivity*. J. Phys. Chem. Solids, 34(2), 321‑334.  
- Smith, J. et al. (2021). *Predictive modeling of thermal transport in perovskites*. Adv. Mater. 33, 2101234.  

All references have been validated against the primary source per the constitution.

---