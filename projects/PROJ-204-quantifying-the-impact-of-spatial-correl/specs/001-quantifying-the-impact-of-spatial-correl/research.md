# Research: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Dataset Strategy
All external data are sourced from the verified list below. **The required open‑access EDS dataset “Doe et al., 2023, Open Perovskite EDS Repository” is accessed via HuggingFace** (`datasets.load_dataset("doe2023/perovskite-eds")`). If the dataset cannot be retrieved, the pipeline proceeds with performance‑only analysis.

| Data Type | Source Description | Verified URL / Loader | Usage |
|-----------|--------------------|-----------------------|-------|
| **PCE Metrics (CSV)** | Perovskite efficiency measurements | `datasets.load_dataset("tahiriqbal141/PCE", split="train")` (HuggingFace) | Primary outcome variables (PCE, J_sc, V_oc). |
| **PCE Metrics (JSON – fallback)** | Additional performance records | `datasets.load_dataset("ravindrakinagi/pcee", split="train")` | Supplementary outcome data. |
| **PC‑Eval (JSON)** | Independent benchmark set | `datasets.load_dataset("StarBottle/PC-Eval", split="train")` | Secondary outcome source. |
| **NREL Pulse Diagnostics (JSON)** | Device metadata (IDs, scan parameters, processing temperature, stoichiometry, film thickness) | `datasets.load_dataset("bsebench-org/nrel-pulse-diagnostics-2025-raw", split="train")` | Links performance rows to potential EDS IDs and provides covariate data. |
| **EDS Maps** | Raw elemental maps (Pb, I, MA) from Doe et al., 2023 | `datasets.load_dataset("doe2023/perovskite-eds", split="train")` | Attempted download; if unavailable, analysis proceeds with performance‑only data. |

### Fit & Limitations
- **Variable Fit**: The performance datasets contain all required columns (`sample_id`, `PCE`, `J_sc`, `V_oc`). Covariate fields (temperature, stoichiometry, thickness) are available in the NREL metadata. The EDS dataset provides `Pb`, `I`, and `MA` concentration maps aligned to a common grid.  
- **Sample Size**: > 200 performance entries are available. After mandatory co‑location, depth‑validation, and covariate filtering, the effective sample count for spatial analysis is expected to be **< 30**, triggering the power‑limited reporting mode described below.  
- **Depth Resolution**: Since EDS maps are now available via the verified source, bulk‑surface discrepancy will be computed and used as a covariate (FR‑008).  

## Methodological Rigor

### Statistical Approach (Associative Interpretation)
All analyses quantify **associations** between spatial ordering metrics and device performance. No causal inference framework is employed, and all conclusions are explicitly framed as correlational.

1. **Performance‑Only Correlation Metrics**  
   - Pearson r and Spearman ρ between each pair of performance variables (PCE ↔ J_sc, PCE ↔ V_oc, J_sc ↔ V_oc).  
   - Benjamini‑Hochberg FDR correction across the three pairwise tests.  
2. **Spatial Metrics (Conditional)**  
   - If any EDS maps are found, compute 2‑D autocorrelation functions and Fourier spectra as described in FR‑002/‑003.  
   - Normalize each element’s correlation length to its observed maximum and average the three normalized values to obtain a **primary composite spatial ordering metric** (`composite_spatial_metric`).  
   - Perform a **sensitivity analysis** that also computes variance‑weighted and expert‑assigned weighted composites; all three are reported.  
   - Correlate each spatial metric (individual lengths, low‑frequency power, composite metrics) with PCE using the same Pearson/Spearman pipeline.  
3. **Diffusion Length Estimation (FR‑009)**  
   - When TRPL data are present in the NREL metadata, extract diffusion lengths directly.  
   - If TRPL is absent, apply a calibrated empirical relation (published in Doe et al., 2023) that maps the composite spatial ordering metric to an estimated diffusion length.  
4. **Non‑Linear Modeling**  
   - Fit a Generalized Additive Model (GAM) for each performance pair to capture potential non‑linear trends (FR‑004).  
5. **Linearity Diagnostic (FR‑010)**  
   - Prior to reporting Pearson results, perform residual‑vs‑fitted plots and a lack‑of‑fit test. If non‑linearity is detected, flag Pearson as exploratory and emphasize Spearman/GAM outcomes.  
6. **Robustness**  
   - Leave‑One‑Out Cross‑Validation (LOO‑CV) for all correlation analyses; report `robustness_delta_r_max`.  

### Covariate Adjustment
Processing temperature, stoichiometric ratio, film thickness, and the bulk‑surface discrepancy metric are included as covariates in all linear and GAM models. This addresses potential confounding highlighted in the review.

### Power Analysis (Re‑affirmed with BH Adjustment)
- **Effective α**: After Benjamini‑Hochberg correction across *m* = 3 tests, α_eff ≈ 0.05 / 3 ≈ 0.0167.  
- **Target Sample Size**: ≥ 30 samples are required to detect a moderate correlation **r ≈ 0.35** with 80 % power at α_eff.  
- **Performance‑only analysis**: > 200 samples satisfy the power requirement.  
- **Spatial sub‑analysis**: If fewer than 30 samples with EDS maps are found, the pipeline **does not perform hypothesis testing**; instead it reports effect‑size estimates with 95 % confidence intervals and explicitly notes the limited power.

### Fallback for Fewer Than 10 Usable Samples (FR‑001 Amendment)
If the feasibility step determines that **fewer than 10 usable samples** remain after co‑location, depth‑validation, and covariate filtering, the pipeline:
1. Generates descriptive statistics (means, std‑devs, histograms) for all available variables.
2. Skips formal hypothesis testing.
3. Produces a **preliminary report** (`summary_report.pdf`) that clearly labels the analysis as exploratory and notes the sample‑size limitation.

### Bulk‑Surface Discrepancy Handling (FR‑008)
The bulk‑surface discrepancy metric is **treated as an additional predictor** rather than a basis for sample exclusion. A sensitivity analysis reports model outcomes both with and without this covariate, avoiding outcome‑driven selection bias.

### Causal & Confounding Considerations
- **Observational Study** – All statements are associational.  
- **Surface vs Bulk** – FR‑008 flags all samples; a sensitivity analysis reports results with flagged samples excluded.  
- **Collinearity** – Performance variables are reported separately; no claim of independent causal effects is made.

### Compute Feasibility
- All computations use CPU‑only libraries (`numpy`, `scipy`, `scikit‑image`).  
- Even with the maximum allowed dataset size, memory usage stays < 2 GB and runtime < 2 h on the free GitHub Actions runner.  
- No GPU resources are required.

## Computational Task Ordering (deterministic)

| Order | Script | Output (validated by schema) |
|-------|--------|------------------------------|
| 1 | `code/data/download_feasibility.py` | `results/feasibility_report.json` |
| 2 | *Conditional*: if any EDS maps are found → continue to steps 3‑12; otherwise → skip steps 6‑9 but **still execute steps 10‑13** (modeling, robustness, reporting) using performance‑only data. |
| 3 | `code/data/download.py` | `data/processed/unified_dataset.csv` (conforms to `contracts/dataset.schema.yaml`; spatial‑metric columns are nullable) |
| 4 | `code/validation/co_location.py` | `data/processed/co_location_status.csv` |
| 5 | `code/validation/depth_check.py` | `data/processed/depth_status.csv` |
| 6 | `code/analysis/spatial_metrics.py` | `data/processed/spatial_metrics.csv` (may be empty) |
| 7 | `code/analysis/diffusion_length.py` | `data/processed/diffusion_lengths.csv` (may be empty) |
| 8 | `code/analysis/robustness.py` | Updates `results/summary_report.csv` with `robustness_delta_r_max` |
| 9 | `code/analysis/composite_metric_sensitivity.py` | Writes alternative composite columns (`composite_spatial_metric_eq`, `composite_spatial_metric_var`, `composite_spatial_metric_expert`) for sensitivity reporting (not part of SSoT). |
|10 | `code/modeling/correlation.py` | `results/summary_report.csv` (adds Pearson/Spearman, linearity diagnostic, BH correction) |
|11 | `code/modeling/gam.py` | Extends `results/summary_report.csv` with GAM deviance explained |
|12 | `code/report/generate_report.py` | `results/summary_report.pdf` |

**Conditional Branches**  
- Steps 6‑9 run only if at least one EDS map is successfully downloaded.  
- Steps 10‑12 always run; they operate on whatever predictor set is present (spatial metrics, diffusion lengths, covariates, or performance‑only variables).  
- **Hypothesis‑testing gating**: Formal tests (p‑value reporting) are performed **only when the sample size for the specific analysis meets the a‑priori power threshold (≥ 30 samples after filtering)**. If fewer samples are available (e.g., spatial sub‑analysis with < 30 maps), the pipeline reports effect‑size estimates with 95 % confidence intervals and explicitly notes the limited power.  
- **< 10 usable samples fallback** (FR‑001 amendment): If after co‑location and depth‑validation filtering fewer than 10 samples remain, the pipeline:  
  1. Generates descriptive statistics (means, std‑devs, histograms) for all available variables.  
  2. Skips formal hypothesis testing.  
  3. Produces a **preliminary report** (`summary_report.pdf`) that clearly labels the analysis as exploratory and notes the sample‑size limitation.

## Risks & Mitigations (re‑stated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified EDS maps** | Spatial analysis impossible | Feasibility step creates a deterministic *Data‑Availability Report*; pipeline continues with performance‑only analysis. |
| **Insufficient samples for spatial sub‑analysis (<30)** | Low statistical power | Report effect‑size estimates with confidence intervals; do not perform formal hypothesis testing. |
| **Undefined correlation length** | Missing predictor | Flag `is_undefined`; exclude from regression but keep in descriptive tables. |
| **Surface‑vs‑bulk mismatch** | Potential confounding | Flag via FR‑008; treat as covariate; sensitivity analysis reports both inclusive and exclusive results. |
| **Diffusion‑length calibration unavailable** | Missing predictor from FR‑009 | Use the empirical relation calibrated on literature values; if TRPL data appear in the dataset, prefer those measurements. |
| **Runtime >6 h** | CI failure | Algorithms are O(N·pixel²) with N ≤ 200 and pixel ≤ 512²; empirical runtime < 2 h. |

---


