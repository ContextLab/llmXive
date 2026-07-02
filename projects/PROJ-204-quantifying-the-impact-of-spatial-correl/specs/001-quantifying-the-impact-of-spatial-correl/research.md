# Research: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Dataset Strategy

The project relies on publicly available datasets. Per the `# Verified datasets` block, the following sources are used. Note that **EDS maps** have no verified source URL; the plan assumes the NREL Perovskite Database and Zenodo (Materials Project) are accessible via the mechanisms described in the spec, but no specific URL is cited for the raw image files.

| Data Type | Source Description | Verified URL / Loader | Usage |
|-----------|--------------------|-----------------------|-------|
| **PCE Metrics** | Perovskite Efficiency Dataset (JSON) | ` | Primary target variable (PCE, J_sc, V_oc) |
| **PCE Metrics (Alt)** | PC-Eval Dataset (JSON) | ` | Fallback/Supplementary performance data |
| **NREL Metadata** | NREL PULSE Diagnostics (JSON) | ` | Cross-reference for device IDs and metadata |
| **EDS Maps** | NREL Perovskite DB / Zenodo | **NO VERIFIED SOURCE** | Raw elemental maps (Pb, I, MA). *Action*: The ingestion script will attempt to fetch based on sample IDs from the verified JSON metadata. If a map is missing, the sample is excluded (FR-001, US-1). **Halt Condition**: If no verified URL is found for EDS maps, the project terminates with a "Data Availability Report". |

**Dataset Fit & Limitations**:
- **Variable Fit**: The verified JSON sources provide performance metrics (PCE, J_sc, V_oc). The EDS maps (Pb, I, MA) are the critical missing link in the verified URL list. The plan assumes these maps are retrievable via the sample IDs found in the JSON metadata. If the JSON metadata does not link to an EDS file, the sample is excluded.
- **Sample Size**: The spec assumes ≥30 samples. If the verified JSON sources yield fewer than 30 matched samples (EDS + PCE), the study will explicitly report this as a power limitation (Assumptions).
- **Depth Resolution**: EDS is surface-sensitive. The plan includes FR-008 to flag samples where bulk-averaged EDS might not correlate with surface-dominated PCE.

## Methodological Rigor

### Statistical Approach
1. **Correlation Metrics**:
 - **Pearson & Spearman**: Calculated between spatial metrics (correlation length, spectral power) and PCE (FR-004).
 - **Multiple Comparison Correction**: Benjamini-Hochberg (BH) procedure applied to p-values when testing multiple elements (Pb, I, MA) to control False Discovery Rate (FR-004).
 - **Non-Linearity**: Generalized Additive Models (GAM) fitted to detect non-monotonic relationships (FR-004).
 - **Multivariate Analysis**: Due to chemical coupling of Pb, I, MA, the plan uses a **composite spatial ordering metric** (average of normalized metrics) or **partial correlation** to control for the other elements. Independent effects of single elements are **not** claimed.

2. **Robustness Checks**:
 - **Leave-One-Out Cross-Validation (LOO-CV)**: Performed to assess sensitivity to outliers (FR-005). The change in correlation coefficient ($\Delta r$) is reported.
 - **Synthetic Validation**: Correlation length extraction accuracy tested against synthetic images with known ground truth (SC-001).
 - **Censored Data Handling**: If correlation length > image dimension, the metric is recorded as a lower bound and excluded from linear regression but included in a censored analysis.

3. **Causal Inference & Assumptions**:
 - **Observational Nature**: This is an observational study. Claims are strictly **associational**. No causal claims (e.g., "spatial ordering *causes* higher efficiency") are made without randomization or identification strategies.
 - **Confounding & Causal Limitations**: The study cannot control for unmeasured confounders (e.g., processing temperature, film thickness). A **Proxy Variable Strategy** is employed: if 'grain_size' is derivable from EDS maps, it is used as a proxy for processing conditions in a partial correlation analysis. If not, the limitation is explicitly stated.
 - **Collinearity**: Elemental maps (Pb, I, MA) are chemically coupled. Independent effects cannot be claimed. The plan reports correlations for the composite metric and acknowledges the inherent collinearity in the discussion.
 - **Measurement Validity**: Correlation length is defined via 1/e decay of the autocorrelation function. Alternative models (Gaussian, power-law) are fitted and compared via AIC (FR-002).

### Power Analysis
- **Minimum Detectable Effect Size (MDES)**: For N=30, 80% power, α=0.05, MDES ≈ r=0.35.
- **Limitation**: If the expected effect size is <0.35, the study is underpowered. The plan will explicitly report this limitation as a primary finding, not a secondary note.

### Compute Feasibility
- **Hardware**: GitHub Actions Free Tier (multi-core CPU, standard RAM allocation).
- **Strategy**:
 - **No GPU**: All operations use CPU-optimized libraries (`scipy`, `numpy`, `scikit-learn`).
 - **Data Sampling**: If the raw dataset exceeds memory, a stratified sample will be taken for initial exploration, but the final analysis uses the full available set (assuming <200MB as per Assumptions).
 - **Image Processing**: 2-D FFT and autocorrelation are computed using `scipy.signal` which is efficient for CPU.
 - **Runtime**: Estimated <2 hours for <200 samples on CPU.

## Computational Task Ordering

1. **Data Feasibility Check**: Verify programmatic link between metadata and EDS images. If failed, terminate and report "Data Availability Report".
2. **Data Ingestion**: Download verified JSONs, attempt EDS fetch, align grids, mask defects (FR-001).
3. **Co-location Validation**: Verify EDS and PCE originate from same device with unique ID (FR-007).
4. **Depth Resolution Validation**: Check EDS depth vs PCE active layer depth (FR-008).
5. **Spatial Metric Extraction**: Compute autocorrelation, fit decay models, calculate spectral power (FR-002, FR-003).
6. **Statistical Modeling**: Calculate correlations, apply BH correction, fit GAMs, perform partial correlation (FR-004).
7. **Robustness**: Perform LOO-CV (FR-005).
8. **Sensitivity Analysis & Conditional Exclusion**: Exclude samples based on sensitivity thresholds (FR-008).
9. **Reporting**: Generate CSV/PDF with ingestion success rate (SC-004) and power limitation report.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **EDS Data Unavailability** | High: No data to analyze. | FR-001: Exclude samples with missing EDS; report exclusion rate; halt if no verified source. |
| **Low Sample Count (<30)** | High: Low statistical power. | Report power limitation explicitly; avoid over-interpreting non-significant results; calculate MDES. |
| **Correlation Length Undefined** | Medium: Missing predictor. | FR-002: Flag as "undefined"; exclude from regression or use lower bound for censored analysis. |
| **Confounding (Surface vs Bulk)** | Medium: Spurious correlations. | FR-008: Flag samples; perform sensitivity analysis excluding flagged samples; use depth-corrected metrics if available. |
| **Chemical Coupling** | High: Spurious inference. | Use composite spatial metrics or partial correlation; acknowledge inability to claim independent effects. |