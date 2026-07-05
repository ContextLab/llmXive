# Research: Brain Network Efficiency and Fluid Intelligence

## Overview

This research plan details the methodology for investigating the relationship between brain network efficiency (global and frontoparietal) and fluid intelligence using the HCP -subject release. The study is observational; all findings will be framed as associational.

## Dataset Strategy

| Dataset | Source/URL | Variables Needed | Verification Status |
|---------|------------|------------------|---------------------|
| HCP 1200-Subject Release (Resting-State fMRI) | https://db.humanconnectome.org/ (Verified via HCP documentation) | Resting-state fMRI time series (minimally preprocessed) | Verified: Contains multiple runs of rs-fMRI per subject. |
| HCP 1200-Subject Release (NIH Toolbox Fluid Intelligence) | https://db.humanconnectome.org/ (Verified via HCP documentation) | NIH Toolbox Fluid Intelligence Score (composite) | Verified: Composite score available in `tfMRI` or `Behavioral` data. |
| Schaefer -ROI Atlas | https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal | Parcellation labels for HCP space | Verified: Publicly available, compatible with HCP MNI space. |
| Schaefer -ROI Atlas | https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal | Parcellation labels for HCP space | Verified: Publicly available, compatible with HCP MNI space. |
| Yeo Atlas (Frontoparietal Definition) | https://surfer.nmr.mgh.harvard.edu/fswiki/CorticalParcellation_Yeo2011 | Network labels for frontoparietal subgraph | Verified: Standard atlas, frontoparietal network defined. |

**Dataset Fit Confirmation**:
- **HCP 1200 Release**: Contains both rs-fMRI (minimally preprocessed) and NIH Toolbox Fluid Intelligence scores for the majority of subjects. No variable mismatch detected.
- **Schaefer/Yeo Atlases**: Publicly available and compatible with HCP data space (MNI).
- **Motion Data**: HCP release includes mean framewise displacement (FD) metrics, required for covariate adjustment.

**Access Strategy**:
- Use HCP API or manual download script (as per HCP access requirements) to fetch data.
- Script will implement retry logic (≥1 retry) and graceful failure if access is restricted.
- Subjects with missing fluid intelligence scores or FD > 0.5 mm will be excluded and logged.

## Methodology

### Phase 1: Data Acquisition and Preprocessing (FR-001, FR-002)
1. **Download**: Fetch rs-fMRI and behavioral data for all subjects (HCP 1200-subject release).
2. **Quality Control**:
   - Exclude subjects with missing fluid intelligence scores.
   - Exclude subjects with mean FD > 0.5 mm.
   - Log counts of excluded subjects.
3. **Preprocessing**:
   - Apply nuisance regression (white matter, CSF, global signal if specified, motion parameters).
   - Apply band-pass filter (0.01–0.1 Hz).
   - **Target**: Ensure mean framewise displacement of preprocessed time series ≤ 0.2 mm.
   - Output: Preprocessed time series per subject.

### Phase 2: Graph Construction and Metric Computation (FR-003, FR-004, FR-013)
1. **Parcellation**:
   - Map preprocessed time series to Schaefer 200-ROI atlas (primary) and 400-ROI (robustness) to address varying resolutions.
   - Compute mean time series per region.
2. **Connectivity Matrix**:
   - Compute Pearson correlation matrix for each subject.
   - **Primary Strategy**: Retain only positive edges (set negative correlations to 0).
   - **Sensitivity Check**: Run a parallel analysis retaining absolute values of negative correlations or including them as negative edges to assess methodological impact on efficiency metrics (addressing Van Wijk et al., 2010 concerns).
3. **Thresholding**:
   - Apply proportional threshold at a moderate density (primary).
 - Also compute for [deferred] and [deferred] (robustness checks) to address the corrected set {0.15, 0.20, 0.25}.
   - Ensure binary graphs have edge density within ±1% of target.
4. **Efficiency Metrics**:
   - Compute **Global Efficiency** for the whole brain graph.
   - Compute **Frontoparietal Efficiency** using Yeo-7 atlas network labels (subgraph defined by frontoparietal nodes).

### Phase 3: Statistical Analysis (FR-005, FR-006, FR-007, FR-009, FR-011)
1. **Correlation Analysis**:
   - Compute Pearson/Spearman correlation between efficiency metrics (global, frontoparietal) and fluid intelligence.
   - Report correlation coefficient, p-value, and 95% confidence interval.
2. **Unique Variance Testing (Residual-Based Approach)**:
   - **Rationale**: Global and Frontoparietal Efficiency are mathematically collinear (subgraph vs. whole). Standard multiple regression cannot distinguish unique contributions.
   - **Method**:
     - Regress Frontoparietal Efficiency on Global Efficiency: `FP_Eff ~ Global_Eff`.
     - Extract residuals (FP_Residuals).
     - Test correlation between `FP_Residuals` and Fluid Intelligence, controlling for Age, Sex, and Mean_FD.
     - Alternatively, use hierarchical regression: Step 1 (Global_Eff + Covariates), Step 2 (Add FP_Eff) and test change in R².
   - **Collinearity Check**: Compute VIF for initial models. If VIF > 5, rely on the residual-based approach. Report VIF for diagnostic purposes.
3. **Permutation Testing (Max-T Procedure)**:
   - **Strategy**: To control Family-Wise Error (FWER) across multiple densities (0.15, 0.20, 0.25) and atlases (200, 400), use a max-T permutation procedure.
   - **Procedure**:
     - For each permutation iteration (target ≥1,000, adaptive to time):
       - Permute subject labels for efficiency metrics relative to fluid intelligence.
       - Compute test statistics for *all* parameter combinations (density × atlas).
       - Record the **maximum** absolute test statistic across the family for this iteration.
     - Compare observed test statistics to the distribution of maximum statistics to derive FWER-corrected p-values.
 - **Runtime Adaptation**: If runtime > 5.5 hours, reduce permutation count to the maximum achievable within the remaining time (min [deferred]), ensuring total analysis time ≤ 6 hours.
4. **Sensitivity Analysis**:
   - Compare results across density thresholds {0.15, 0.20, 0.25}.
 - Primary finding: [deferred] density. Others: robustness checks.

### Phase 4: Reporting (FR-008, FR-010)
- Generate report with:
  - Correlation/regression tables.
  - Figures: Scatter plots (efficiency vs. intelligence), sensitivity analysis plots.
  - **Mandatory Phrase**: "Findings are associational and do not imply causation due to the observational study design."
  - **Citation**: NIH Toolbox Fluid Intelligence validation study (Gershon et al., 2013 or similar).

## Statistical Rigor & Power

- **Multiple Comparison Correction**: Max-T permutation testing with FWER correction applied across all hypothesis tests (global/frontoparietal, densities, atlases).
- **Sample Size / Power**:
  - Target: ≥80% power to detect r=0.25 at α=0.05.
  - **Sensitivity Analysis**: Power will be calculated across a range of effect sizes (r=0.1 to r=0.3) and noise assumptions to determine the Minimum Detectable Effect Size (MDES) for N=500 and N=1200.
  - With N=500 (sampled), power for r=0.25 is >90%.
  - With N=1200 (full), power is >99%.
  - If full analysis exceeds 6h, sampling to 500 subjects ensures power >80% and runtime compliance.
- **Causal Inference**: Explicitly stated as observational; no causal claims.
- **Measurement Validity**: NIH Toolbox Fluid Intelligence instrument validated in Gershon et al. (2013) and others.
- **Collinearity**: VIF computed for diagnostic; residual-based approach used to isolate unique variance in the final model.

## Compute Feasibility Strategy

- **CPU-Only**: All operations (preprocessing, graph metrics, stats) use CPU-optimized libraries (`nilearn`, `networkx`, `scipy`).
- **Memory Management**:
  - Stream data where possible.
  - Process subjects in batches.
  - Sample to a representative subset if the full dataset exceeds 7GB RAM or 6h runtime.
- **Runtime Adaptation**:
  - Permutation count dynamically reduced if time > 5.5h.
  - Parallel processing limited to 2 cores (GitHub Actions limit).
- **Library Pins**: Use CPU-wheel compatible versions of `torch` (if needed for graph, but likely `networkx` suffices), `numpy`, `scipy`.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| HCP access restricted | Retry logic (≥1 retry); fallback to cached data if available; log failure. |
| Preprocessing failure for some subjects | Skip affected subjects; log count; continue with ≥90% cohort. |
| Runtime exceeds 6h | Sample to 500 subjects; reduce permutation count; log rationale. |
| VIF > 5 | Use residual-based approach to isolate unique variance; report VIF for diagnostics. |
| Missing variables | Explicitly state mismatch; do not proceed with incomplete data. |
| Negative edge bias | Run sensitivity analysis retaining/transforming negative edges. |