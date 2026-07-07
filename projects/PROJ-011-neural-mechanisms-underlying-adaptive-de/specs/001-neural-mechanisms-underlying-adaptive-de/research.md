# Research: Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

## Research Question

How do neural signatures of feedback discrepancy in the dlPFC, ventral striatum, and ACC correlate with individual differences in computational belief-updating rates during adaptive decision-making?

## Dataset Strategy

### Verified Datasets
The following datasets have been verified for reachability and format. The plan will strictly utilize these sources.

| Dataset Name | Variable Fit | URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **OpenNeuro ds003694** | Contains raw fMRI NIfTI files (bold) and behavioral logs for social feedback tasks. Includes derived motion logs. | `https://openneuro.org/datasets/ds003694` (Loader: `openneuro-py` or `datalad`) | **Verified** |

### Critical Data Gap Analysis (Resolved)
**Resolution**: The specification originally required raw fMRI NIfTI for full preprocessing (FR-001). The verified dataset (OpenNeuro ds003694) provides **raw NIfTI files** and behavioral logs.
- **Action**: The plan will execute full preprocessing (motion correction, normalization, smoothing) on the raw NIfTI files.
- **Motion QC**: Motion parameters will be extracted from the derived logs or calculated from the raw data to enable SC-001 (Exclusion > 3mm/10% volumes).
- **Voxel-wise vs ROI**: The plan will perform **voxel-wise** permutation testing (FR-004) on the full 4D volumes, followed by ROI extraction for correlation analysis.

### Variable Mapping
| Study Variable | Required Source | Verified Dataset Availability |
| :--- | :--- | :--- |
| Private Belief Rating | Behavioral Log | **Available** (OpenNeuro logs) |
| Social Feedback Rating | Behavioral Log | **Available** (OpenNeuro logs) |
| Choice Data | Behavioral Log | **Available** (OpenNeuro logs) |
| dlPFC Time-Series/Beta | fMRI NIfTI | **Available** (Raw NIfTI) |
| Ventral Striatum Time-Series/Beta | fMRI NIfTI | **Available** (Raw NIfTI) |
| ACC Time-Series/Beta | fMRI NIfTI | **Available** (Raw NIfTI) |
| Motion Parameters | fMRI Logs | **Available** (Derived or Calculated) |

## Statistical Methodology

### 1. Belief Updating Model (Hierarchical Bayesian)
- **Model**: Hierarchical Rescorla-Wagner variant.
- **Parameters**: $\alpha$ (learning rate), $\beta$ (precision).
- **Inference**: `pymc` with `numpyro` backend (CPU). **4 chains, 2000 samples** (Target N=30).
- **Validation**: Posterior predictive checks on held-out trials. Target accuracy ≥ 60%.
- **Multiple Comparisons**: Not applicable for model fitting, but parameter uncertainty (HDI) must be reported.
- **Power**: Target N=30 provides [deferred] power for r=0.3. If N < 30, power limitation is reported.
- **Convergence**: Monitor R-hat. If R-hat > 1.01 after 3 restarts, exclude participant.

### 2. Neural-Behavioral Correlation (Tautology Mitigation)
- **Method**: Partial Pearson/Spearman correlation + **Leave-One-Subject-Out (LOSO) Cross-Validation**.
- **Variables**: $X$ = Neural activation (beta weights from GLM for feedback discrepancy), $Y$ = $\alpha$ (updating rate), $Z$ = Input discrepancy (control).
- **Tautology Break**: The LOSO approach ensures the correlation is not driven by the shared input signal. Additionally, the partial correlation explicitly controls for the input discrepancy magnitude.
- **Assumption**: Observational study. Claims will be framed as **associational**.
- **Collinearity**: Acknowledge that input discrepancy and updating rate may be definitionally related. Report descriptive statistics.
- **Confound Control**: GLM includes motion parameters and their derivatives, along with aCompCor (multiple components). to control for physiological noise and motion residuals.

### 3. Voxel-Wise Inference (FR-004/SC-004)
- **Method**: General Linear Model (GLM) with parametric modulation.
- **Correction**: Permutation testing (a sufficient number of permutations) with **FDR correction across the full brain volume**.
- **Sample Size/Power**: Power analysis deferred to implementation. Acknowledge limitation if $N$ is small (<30).
- **Confound Control**: GLM includes motion parameters and their derivatives along with Global Signal Regression. (if available) to control for physiological noise.

## Computational Constraints & Decisions

- **Library Choice**: `pymc` (CPU backend with `numpyro`) to ensure CPU-only compatibility.
- **Data Sampling**: If dataset size > 7GB RAM, will sample [deferred] of participants or downsample time-series.
- **Runtime**: Total pipeline limited to hours. MCMC chains limited to a sufficient number of samples per participant to ensure convergence, as outlined in [citation]. The research question remains: [research question]. The method employed is: [method]..
- **Validation**: `data_validation.py` script ensures specific derived variables exist before processing.
- **Preprocessing**: Use lightweight `nibabel`/`nilearn` pipelines for motion correction and normalization to fit within 6h.

## Decision Log

| Decision | Rationale | Impact |
| :--- | :--- | :--- |
| **Use OpenNeuro ds003694** | Verified to contain raw NIfTI and behavioral logs for social feedback. | Resolves modality mismatch. Enables full preprocessing. |
| **Voxel-Wise FDR** | Dataset supports full volume processing. | FR-004/SC-004 met as specified. |
| **LOSO Cross-Validation** | Prevents tautological correlation between alpha and beta derived from same signal. | Ensures scientific soundness. |
| **Derived Motion QC** | Use derived logs or calculate from raw to enable SC-001. | SC-001 measurable. |
| **pymc/numpyro** | CPU-optimized, compatible with GitHub Actions. | Ensures feasibility within 6h. |
| **N=30 Target** | Provides [deferred] power for r=0.3. | MCMC budget tuned to N=30. |
| **Confound Control** | GLM includes motion + aCompCor. | Reduces false positives from noise. |
