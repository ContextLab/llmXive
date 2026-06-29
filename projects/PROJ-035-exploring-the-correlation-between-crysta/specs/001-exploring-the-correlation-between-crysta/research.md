# Research: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

## Dataset Strategy

**Critical Verification Note**: The `spec.md` requires data from the **Materials Project API** and **curated literature datasets** (e.g., NIST). The provided `# Verified datasets` block **does not contain** verified URLs for these specific materials science sources. Per instruction, no URLs are fabricated. The implementation MUST verify these sources against the primary providers (Materials Project, NIST) before the `Verified Accuracy` gate (Constitution Principle II).

| Dataset Name | Required Variables | Verified Source Status | Load Method |
|--------------|-------------------|------------------------|-------------|
| Materials Project Structures | `material_id`, `crystal_structure`, `stoichiometry` | **NO verified source in block** (Must verify mp.org API) | `pymatgen.ext.matproj` (API Key required) |
| Thermal Conductivity Data | `material_id`, `thermal_conductivity` | **NO verified source in block** (Must verify NIST/Lit) | Manual merge / API (if available) |

**Variable Fit Assessment**:
- **Predictors**: Octahedral tilting angles, bond-length variance, tolerance factor, unit cell volume. (Derivable from structure).
- **Outcome**: Thermal conductivity (W/m·K).
- **Gap**: If the literature dataset lacks `material_id` linkage to Materials Project IDs, the merge will fail. Implementation must verify ID mapping strategy during Phase 0.

## Statistical Methodology

### 1. Correlation Analysis (FR-003, FR-004)
- **Metrics**: Pearson (linear) and Spearman (monotonic) coefficients.
- **Correction**: Benjamini-Hochberg procedure applied to all descriptor p-values to control False Discovery Rate (FDR) at q < 0.05.
- **Rationale**: Multiple testing across 4+ descriptors inflates Type I error; FDR is standard for exploratory materials informatics.

### 2. Regression Modeling (FR-005, FR-010)
- **Model**: Multiple Linear Regression (OLS).
- **Validation**: 5-fold Cross-Validation (stratified by material class if possible, otherwise random).
- **Collinearity**: Variance Inflation Factor (VIF) calculated for all predictors.
  - **Threshold**: VIF > 5 triggers "descriptive-only" flag (FR-005).
  - **Rationale**: Structural descriptors (e.g., volume vs. bond length) are often definitionally related; independent effects cannot be claimed if collinear.
- **Power Analysis**: Post-hoc power analysis performed on final sample size (N) and observed effect size (R²).
  - **Target**: N ≥ 40 (4 predictors × 10) minimum; N ≥ 80 recommended.
  - **Deferral**: Exact threshold `[deferred]` until data ingestion confirms N.

### 3. Causal Framing (FR-006)
- **Constraint**: All text output MUST use "associated with", "correlated with", "predicts".
- **Prohibited**: "cause", "causes", "effect", "determines", "deterministic".
- **Rationale**: Observational study design does not support causal inference regardless of statistical significance.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Memory**: `pymatgen` structure objects are memory-intensive but manageable for <10k entries. Dataframes will be subset to required columns only.
- **Runtime**:
  - Ingestion: ~30 mins (API rate limits + retries).
  - Descriptors: ~1 hour (pymatgen calculations are CPU bound).
  - Analysis: <10 mins (scikit-learn is efficient).
  - Total: <2 hours (well within 6h limit).
- **Libraries**: `pymatgen`, `scikit-learn`, `pandas` all support CPU-only execution. No CUDA/mixed-precision code used.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| Use Materials Project API (mp.org) | Spec FR-001 mandates it; no verified alternative in provided block. |
| CPU-only Execution | Constraint FR-008; CI environment lacks GPU. |
| Benjamini-Hochberg Correction | Spec FR-004; controls FDR better than Bonferroni for exploratory work. |
| VIF Threshold 5 | Standard rule of thumb for multicollinearity in regression (FR-005). |
| Associational Language | Spec FR-006; aligns with observational study design. |
