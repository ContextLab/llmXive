# Research: Statistical Power Analysis of Openly Available fMRI Datasets

## Dataset Strategy

| Dataset Name | Source URL | Access Method | Variables Available | Fit for Purpose | Notes |
|--------------|------------|---------------|---------------------|-----------------|-------|
| OpenNeuro ds000030 | https://openneuro.org/datasets/ds000030 | `bidslib` / `openneuro-cli` | Motor Task (Raw BIDS) | ✅ YES | Verified; Motor paradigm; N=30+ |
| OpenNeuro ds000206 | https://openneuro.org/datasets/ds000206 | `bidslib` / `openneuro-cli` | Working Memory (Raw BIDS) | ✅ YES | Verified; Working Memory paradigm; N=40+ |
| OpenNeuro ds000117 | https://openneuro.org/datasets/ds000117 | `bidslib` / `openneuro-cli` | Emotional Face (Raw BIDS) | ✅ YES | Verified; Emotional Face paradigm; N=20+ |
| OpenNeuro ds000247 | https://openneuro.org/datasets/ds000247 | `bidslib` / `openneuro-cli` | Auditory Oddball (Raw BIDS) | ✅ YES | Verified; Auditory paradigm; N=30+ |
| OpenNeuro ds001141 | https://openneuro.org/datasets/ds001141 | `bidslib` / `openneuro-cli` | Visual Motion (Raw BIDS) | ✅ YES | Verified; Visual Motion paradigm; N=25+ |
| OpenNeuro Discovery Script | | `openneuro-api` | Metadata only | ✅ YES | Used to discover additional datasets; execution capped at a minimal threshold for MVP |

**Rationale**: These are the ONLY verified datasets per the user-provided block and OpenNeuro API. They provide raw BIDS data necessary for noise estimation and ROI structure. The plan uses these to estimate noise characteristics and ROI masks, then generates synthetic data with known ground truth for the power analysis. This satisfies the requirement for raw data processing (FR-002) while enabling the known-truth power analysis. **The "up to 15" requirement in FR-001 is addressed by a discovery script, but execution is capped at these 5 verified datasets for the MVP to ensure feasibility.** The multi-paradigm target remains an aspirational goal for future expansion.

## Methodological Rationale

### Statistical Approach
- **Known-Truth Simulation**: Instead of relying on circular split-half consistency, the system generates synthetic fMRI time-series with a **known ground-truth effect size (Cohen's d)**. The effect is embedded in the noise derived from real data.
- **Split-Half Validation**: Randomly partition subjects into train/test sets (50/50 split). Estimate effect size (Cohen's d) on train set; test significance (p < alpha) on held-out test set. **Replication Success** = 1 if the test set correctly detects the known effect (p < alpha) AND the direction matches the known truth. This measures true statistical power (probability of detection).
- **Bootstrapping**: 50+ iterations per sample size to generate stable empirical probability of replication.
- **Logistic Regression**: Model replication success (binary) as outcome; predictors: sample size, smoothing kernel (temporal), SNR level (input), effect size group (Null, Small, Medium, Large). Use `statsmodels` for CPU-optimized fitting.
- **Multiple Comparison Correction**: Apply Benjamini-Hochberg FDR to final model results across 5 paradigms to control family-wise error rate.
- **Alpha Sensitivity Analysis**: Sweep alpha values across a range of conventional thresholds to verify robustness of power curves to threshold selection.

### Power & Sample Size Justification
- **Effect Size Grid**: Simulations run for d=0.0 (Null), 0.2 (Small), 0.5 (Medium), 0.8 (Large), 1.0 (Very Large). This allows explicit measurement of power for specific effect sizes.
- **Null Effect Baseline**: The d=0 condition ensures the plan distinguishes between "low power" (high N, low d, low detection) and "null effect" (d=0, detection rate ~ alpha).
- **Power Limitation**: For paradigms with small effect sizes, even N=100 may yield low replication rates — this is a feature, not a bug, reflecting real-world challenges.

### Causal Inference Assumptions
- **Observational Data**: All datasets are observational; no randomization of participants. Claims framed as **associational** only (e.g., "larger sample sizes are associated with higher replication rates").
- **No Causal Claims**: Does not claim preprocessing choices *cause* changes in power; only reports observed associations.

### Measurement Validity
- **Effect Size Metric**: Cohen's d computed from GLM contrast estimates; standard in neuroimaging literature.
- **Replication Metric**: Correct detection of known ground truth (True Positive Rate) aligns with the definition of statistical power.

### Predictor Collinearity
- **SNR as Input**: SNR is a *simulation parameter* (input), not a derived predictor. This avoids the circularity of using derived noise to predict power derived from the same noise.
- **Interaction Terms**: Logistic regression includes interaction terms (Sample Size × Smoothing Kernel) to model non-linear relationships.

## Compute Feasibility

### CPU-First Strategy
- **Preprocessing**: Lightweight ROI extraction (`roi_extractor.py`) using `nilearn` to extract time-series from anatomical masks. **No full fMRIPrep** due to compute constraints (2 CPU, 7 GB RAM). This is a necessary adaptation to meet FR-002's intent (standardized preprocessing) while remaining feasible on the target platform.
- **Smoothing**: Temporal smoothing of ROI time-series (Gaussian kernel over time points) to test sensitivity to temporal autocorrelation.
- **GLM Fitting**: `nilearn.glm.first_level.FirstLevelModel` with `noise_model='ar1'` and `standardize=False` for CPU efficiency.
- **Bootstrapping**: Parallelized via `joblib` with `n_jobs=2` (matches 2 CPU cores); each iteration independent.
- **Memory Management**: Stream datasets via `datasets.load_dataset(..., streaming=True)`; sample subjects on-the-fly to stay within available RAM constraints.

### GPU Escape Hatch (Not Needed)
- **No GPU Required**: All methods (GLM, logistic regression, bootstrapping) are CPU-tractable. No transformer/diffusion models or CUDA kernels planned.

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| fMRIPrep fails on GitHub Actions | **Not used**; pipeline uses lightweight ROI extraction as a CPU-tractable alternative |
| Dataset corrupted/incomplete | Skip affected subjects; log warning; fail job if <10 valid subjects remain |
| GLM fails to converge | Discard iteration; increment failure counter; flag result as "Unreliable" if >20% failures |
| Memory overflow | Stream data; sample subjects dynamically; clamp requested N to available data |
| Power curve non-monotonic | Investigate; may indicate effect size near zero or noise dominance; report honestly |

## Ethical Considerations

- **No PII**: All OpenNeuro datasets are anonymized; no personally identifiable information processed.
- **Reproducibility**: All code, seeds, and data sources documented; results fully reproducible.
- **Transparency**: Report all failures, limitations, and assumptions (e.g., small effect sizes, observational data, 5-paradigm MVP scope).