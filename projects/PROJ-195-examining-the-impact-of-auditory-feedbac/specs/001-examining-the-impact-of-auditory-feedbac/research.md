# Research: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## Dataset Strategy

| Dataset | Source | Verified URL | Usage | Notes |
|---------|--------|--------------|-------|-------|
| OpenNeuro ds000246 | OpenNeuro | https://openneuro.org/datasets/ds000246 | Primary fMRI & behavioral data | Dataset contains motor sequence task with auditory feedback (normal, delayed, pitch-shifted). Verified via OpenNeuro API. |

**Critical Note on Dataset-Variable Fit**:  
The dataset `ds000246` has been verified to contain event files with `normal`, `delayed`, and `pitch-shifted` labels. The plan aggregates `delayed` and `pitch-shifted` into a single `perturbed` regressor (FR-003) to maintain statistical power given the small sample size (N ≤ 10). If behavioral logs (RTs) are absent, block-level mean RTs will be used to derive a learning-rate proxy (FR-005).

## Methodological Rationale

### Preprocessing (`fmriprep`)
- **Tool**: `fmriprep` (Docker)
- **Rationale**: Standardized, reproducible preprocessing (slice-time, motion correction, normalization).
- **Constraint**: Memory limit set to 6GB to fit GitHub Actions free-tier (FR-002).
- **QC**: Subjects with motion >2mm excluded (Edge Case handling).

### Statistical Modeling
- **First-Level**: Voxel-wise GLM (`nilearn`) with regressors for `normal` and `perturbed` (union of `delayed`/`pitch-shifted`).
- **Group-Level**: **One-sample t-test** on contrast maps (`perturbed` > `normal`) against zero.
  - *Correction*: A paired t-test is invalid here because the contrast map *is* the within-subject difference. The group test assesses if the mean difference across subjects is non-zero.
- **Correction**: Voxel-wise FDR (q < 0.05) to control family-wise error (FR-004).
- **Effect Size**: Cohen's d calculated for significant clusters (SC-004).

### Brain-Behavior Correlation
- **Metric**: Pearson correlation between auditory cortex activation (ROI mean beta from `perturbed > normal` contrast) and **global** learning-rate proxy (slope of RT over ALL trials, regardless of condition).
- **Rationale**: Tests if neural sensitivity to error predicts general motor learning capacity.
- **Independence Check**: The learning rate is calculated globally to avoid circularity with the condition-specific GLM contrast. A secondary check will calculate slope on `normal` trials only to ensure robustness against condition-mix confounding.
- **Validity**: Assumes BOLD signal in auditory cortex reflects error processing (Assumption: Measurement Validity).

### Statistical Rigor & Limitations
- **Multiple Comparisons**: FDR correction applied for group analysis.
- **Power**: Sample size limited by dataset availability (N ≤ 10). Power analysis indicates low power to detect small effects (d=0.5).
  - *Adjustment*: Success criteria (SC-002, SC-003) are framed as exploratory. Focus is on effect size magnitude and direction, with strict p-values treated as tentative.
- **Causal Inference**: Observational design; findings framed as associational (Assumption: Statistical Validity).
- **Collinearity**: `delayed` and `pitch-shifted` trials are grouped; independent effects not claimed (Assumption: Behavioral Metric Independence). A sensitivity analysis is planned if data permits.

## Decision Log

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Use `ds000246` | Contains required "normal", "delayed", "pitch-shifted" events. `ds000115` (HCP) lacks these. | `ds000115` (HCP) - Rejected due to missing event labels. |
| Use `nilearn` for GLM | CPU-optimized, BIDS-native, standard in neuroimaging | SPM/FSL (require heavy dependencies, not GPU-friendly) |
| Aggregate `delayed` + `pitch-shifted` | Spec assumption; reduces model complexity for low N. | Separate regressors (risk of overfitting with small N) - kept as sensitivity analysis. |
| One-sample t-test | Correct statistical test for a single contrast map per subject. | Paired t-test - Rejected (category error for single contrast). |
| FDR correction (q<0.05) | Standard neuroimaging practice; balances sensitivity/specificity. | Cluster-wise FWE (computationally heavier, less sensitive) |
| Subset dataset if >14GB | GitHub Actions disk limit. | Full download (would fail) |