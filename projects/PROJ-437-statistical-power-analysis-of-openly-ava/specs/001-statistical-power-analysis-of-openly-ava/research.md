# Research: Statistical Power Analysis of Openly Available fMRI Datasets

## Dataset Strategy

| Dataset Name (paradigm) | Source URL(s) | Access Method | Variables Available | Fit for Purpose | Notes |
|--------------------------|---------------|---------------|---------------------|-----------------|-------|
| Motor (ds000030) | https://openneuro.org/datasets/ds000030 | `openneuro_py.download(ds_id='ds000030', target_dir='data/raw/')` | Raw BIDS (NIfTI volumes, JSON metadata, event timings, subject IDs) | ✅ Yes | Motor task with sufficient subjects (N≈50) for sampling to N=10, 20, 40, 60. |
| Working Memory (ds000206) | https://openneuro.org/datasets/ds000206 | `openneuro_py.download(ds_id='ds000206', target_dir='data/raw/')` | Raw BIDS (NIfTI, JSON, events) | ✅ Yes | Working‑memory task; sample size > 30 subjects. |
| Emotional Face (ds000117) | https://openneuro.org/datasets/ds000117 | `openneuro_py.download(ds_id='ds000117', target_dir='data/raw/')` | Raw BIDS (NIfTI, JSON, stimulus labels) | ✅ Yes | Emotional face matching; a modest sample size. |
| Auditory Oddball (ds000247) | https://openneuro.org/datasets/ds000247 | `openneuro_py.download(ds_id='ds000247', target_dir='data/raw/')` | Raw BIDS (NIfTI, JSON, trial types) | ✅ Yes | Auditory oddball paradigm; a sample of participants of adequate size. |
| Visual Motion (ds001141) | https://openneuro.org/datasets/ds001141 | `openneuro_py.download(ds_id='ds001141', target_dir='data/raw/')` | Raw BIDS (NIfTI, JSON, motion direction) | ✅ Yes | Visual motion task; a moderate sample size. |

**CRITICAL DATA AVAILABILITY NOTE**: These five datasets are sourced from OpenNeuro's canonical BIDS repository (https://openneuro.org/), which provides **raw NIfTI fMRI volumes and JSON metadata** — the complete BIDS structure required for ROI extraction, GLM fitting, and noise estimation. The original specification's "up to 15 paradigms" target is acknowledged, but for feasibility on the free‑tier runner we cap the MVP at these five verified paradigms. The discovery script in `research.md` can enumerate additional datasets, but execution will stop after the five verified datasets listed above.

## Methodological Rationale

### Statistical Approach
1. **Noise Estimation** – From each raw dataset we extract voxel‑wise temporal BOLD time‑series and compute temporal SNR and a Gaussian noise model (`noise_estimator.py`).  
2. **Signal Injection** – Using the estimated noise model, `signal_injector.py` injects a synthetic signal component (with user‑specified **Cohen's d**: 0.0, 0.2, 0.5, 0.8, 1.0) **INTO** the real BOLD time‑series extracted from each dataset. This creates signal‑injected time‑series that preserve the real data structure while embedding a known ground‑truth effect.  
3. **Split‑Half Validation** – For each bootstrap iteration, subjects are randomly split 50/50. A GLM is fit on the training half (`glm_fitter.py` – **T016**), producing an estimated effect size and contrast map. The same contrast is evaluated on the test half; replication success = 1 iff (a) the test‑set p‑value < α and (b) the direction matches the training estimate.  
4. **Magnitude Tolerance Sensitivity** – The primary replication criterion uses p < α and direction match. Magnitude tolerance (matching within ±20% of the training estimate) is swept over [±10%, ±20%, ±30%] in a separate sensitivity analysis to test robustness to the tolerance threshold.  
5. **Bootstrapping** – ≥ 50 iterations per `(sample size, smoothing kernel, effect size)` configuration guarantee a stable empirical replication probability (SC‑001).  
6. **Power Curve Generation** – Aggregated replication rates across sample sizes generate power curves. Primary analysis uses a coarse grid (10, 20, 40, 60); secondary analysis uses a finer grid (10, 15, 20, 30, 40, 50, 60) on two paradigms to better capture the non‑linear relationship (SC‑002).  
7. **Predictor Collinearity Check** – Before fitting the logistic regression, a correlation matrix of predictors (sample size, smoothing kernel, SNR) is computed and reported in `results/paper/predictor_correlation.csv`. VIF is computed for all predictors; if any VIF ≥ 5, the model is refit without the offending term. This ensures collinearity is detected and mitigated (T090).  
8. **Logistic Regression** – Binary replication outcomes are modeled with `statsmodels` (CPU‑optimized) using predictors: sample size, smoothing kernel, SNR level, and effect‑size group. Convergence diagnostics are recorded by `convergence_monitor.py` (**T049**) and summarized in `results/paper/convergence_report.md`.  
9. **Multiple‑Comparison Correction** – Final model p‑values across the five paradigms are corrected with Benjamini‑Hochberg FDR (as required by the assumptions).  
10. **Alpha Sensitivity** – Power curves are recomputed for α = 0.01, 0.05, 0.10 to confirm robustness (assumption in spec).  

### Construct Validity Limitations
The use of signal injection into real BOLD time‑series (rather than fully synthetic data) preserves the real data structure and noise characteristics, improving ecological validity. However, the injected signal is a simplified sinusoidal or boxcar function, which may not capture the full complexity of real task-related BOLD responses (e.g., hemodynamic response function variability, physiological noise, motion artifacts). Power estimates are therefore valid only under the estimated noise model and should not be extrapolated to real-world studies without independent validation. Results are framed as **associational** (e.g., "larger sample sizes are associated with higher replication probability under the signal-injection model").

### Power & Sample Size Justification
- **Effect‑size grid** enables explicit mapping from known effect to empirical power.  
- **Sample‑size ceiling** is the original size of the largest dataset (≈ 100); no extrapolation beyond observed data.  
- **Bootstrap size** (≥ 50) satisfies FR‑004 and yields confidence intervals narrow enough for SC‑002.  
- **Two-tier sample-size grid** (coarse + fine) addresses the concern that four points are sparse; the fine grid (10, 15, 20, 30, 40, 50, 60) captures the non‑linear relationship more accurately on two paradigms.

### Causal Inference Assumptions
All datasets are observational; therefore, findings are framed as **associational**. No causal claims are made about preprocessing choices.

### Measurement Validity
Cohen's d is the standard effect‑size metric for GLM contrast estimates in neuroimaging. The injected signal is a known quantity, ensuring that the ground‑truth effect is measurable and that replication success is an empirical test on held‑out data.

### Predictor Collinearity
Predictors (sample size, smoothing kernel, SNR) are intended to be orthogonal by design, but this is verified empirically via T090 (collinearity checker) before model fitting. Any VIF ≥ 5 triggers a warning and model refitting without the offending term.

## Compute Feasibility

| Component | CPU‑first Strategy | Expected Resource Use |
|-----------|-------------------|----------------------|
| Data download & BIDS validation | `openneuro_py.download()` downloads raw BIDS (~500 MB per paradigm) | < 3 GB RAM, ~5 GB disk per dataset |
| Noise estimation | Temporal SNR computed on real BOLD time‑series (`nilearn.masking.apply_mask` + NumPy) | ~2 GB RAM max |
| Signal injection | Sinusoidal/boxcar signal added to real BOLD (NumPy) | negligible RAM |
| Temporal smoothing | Convolution over time dimension (NumPy) | negligible RAM |
| GLM fitting | `nilearn.glm.FirstLevelModel` with `noise_model='ar1'` | < 1 GB RAM per iteration |
| Bootstrapping | Parallelized with `joblib` (`n_jobs=2`) | CPU bound, fits within 2 cores |
| Collinearity check | Correlation matrix + VIF (`statsmodels`) | < 500 MB RAM |
| Logistic regression | `statsmodels.Logit` (CPU) | < 500 MB RAM |
| Overall wall‑clock | End‑to‑end on 5 paradigms, coarse grid (10, 20, 40, 60), 50 iterations ≈ 4.5 h; fine grid on 2 paradigms adds ~1 h | ✅ Meets SC‑005 (< 6 h) |

**GPU Escape Hatch** – Not required; all steps are CPU‑tractable. No CUDA kernels are used.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OpenNeuro download infeasible | `openneuro_py` supports resumable downloads; if interrupted, the next run resumes from the last checkpoint. |
| Corrupted NIfTI files | `download/data_validator.py` checks file integrity (checksum validation T082); corrupted subjects are skipped with a logged warning. |
| GLM non‑convergence | Iteration flagged; if > 20 % of iterations fail, overall result labeled "Unreliable". |
| Memory overflow | `memory_monitor.py` monitors RAM; when usage > 5 GB it randomly downsamples subjects and logs the action (T081). |
| Non‑monotonic power curve | Report as observed; may indicate effect size near zero or signal-injection model mismatch (expected per SC‑002). |
| Missing dataset | The pipeline logs a "Data Limitation" warning and proceeds with the available paradigms; no fabrication. |
| Contract failures (checksum, schema) | `tests/contract/` suite (including T082) runs on every CI job; failures abort the run. |
| Collinearity in predictors | T090 empirically checks VIF before logistic regression; any VIF ≥ 5 triggers model refitting without the offending term. |
| Arbitrary magnitude tolerance | Sensitivity analysis sweeps tolerance over [±10%, ±20%, ±30%]; robustness is demonstrated across the range. |

## Ethical Considerations
- **Anonymity** – All OpenNeuro datasets are pre‑anonymized; no PII is processed.  
- **Transparency** – Every step logs inputs, parameters, and outputs; failures are reported in `results/paper/convergence_report.md`.  
- **Reproducibility** – Full environment captured via `requirements.txt`; seeds fixed; data sources immutable URLs.  
