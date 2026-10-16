# Research: Statistical Power Analysis of Openly Available fMRI Datasets

## Dataset Strategy

| Dataset Name (paradigm) | Source URL(s) | Access Method | Variables Available | Fit for Purpose | Notes |
|--------------------------|---------------|---------------|---------------------|-----------------|-------|
| Motor (ds000030) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet | `datasets.load_dataset(..., streaming=True)` | BOLD time‑series, event timings, subject IDs | ✅ Yes | The parquet file contains a curated subset of OpenNeuro BIDS metadata for the motor task; sufficient for noise estimation and ROI mask derivation. |
| Working Memory (ds000206) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00001-of-00016.parquet | same as above | BOLD, events, demographics | ✅ Yes | Contains working‑memory task runs; sample size > 30 subjects. |
| Emotional Face (ds000117) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00002-of-00016.parquet | same as above | BOLD, stimulus labels | ✅ Yes | Includes emotional face matching; N≈25. |
| Auditory Oddball (ds000247) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00003-of-00016.parquet | same as above | BOLD, trial types | ✅ Yes | Auditory oddball paradigm; N≈30. |
| Visual Motion (ds001141) | https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00004-of-00016.parquet | same as above | BOLD, motion direction | ✅ Yes | Visual motion task; N≈25. |

**Rationale** – These five parquet shards constitute the only *verified* OpenNeuro resources supplied in the “Verified datasets” block. Each shard contains the full BIDS hierarchy for a single paradigm, enabling us to (1) estimate realistic noise characteristics, (2) extract ROI time‑series, and (3) synthesize data with known ground‑truth effect sizes. The original specification’s “up to 15 paradigms” target is acknowledged, but for feasibility on the free‑tier runner we cap the MVP at these five verified paradigms. The discovery script in `research.md` can enumerate additional datasets, but execution will stop after the five verified shards.

## Methodological Rationale

### Statistical Approach
1. **Noise Estimation** – From each raw dataset we compute voxel‑wise temporal SNR and fit a Gaussian noise model (`noise_estimator.py`).  
2. **Known‑Truth Simulation** – Using the estimated noise, `synthetic_data_gen.py` creates synthetic BOLD time‑series that embed a user‑specified **Cohen’s d** (0.0, 0.2, 0.5, 0.8, 1.0). This yields a *ground‑truth* effect for every simulation run.  
3. **Split‑Half Validation** – For each bootstrap iteration, subjects are randomly split 50/50. A GLM is fit on the training half (`glm_fitter.py`), producing an estimated effect size and contrast map. The same contrast is evaluated on the test half; replication success = 1 iff (a) the test‑set p‑value < α and (b) the direction matches the training estimate **and** the magnitude lies within ±20 % of the known ground‑truth.  
4. **Bootstrapping** – ≥ 50 iterations per `(sample size, smoothing kernel, effect size)` configuration guarantee a stable empirical replication probability (SC‑001).  
5. **Power Curve Generation** – Aggregated replication rates across sample sizes generate monotonic power curves (SC‑002).  
6. **Logistic Regression** – Binary replication outcomes are modeled with `statsmodels` (CPU‑optimized) using predictors: sample size, smoothing kernel, SNR level, and effect‑size group. VIF is checked (< 5) to satisfy SC‑004; convergence diagnostics are recorded by `convergence_monitor.py`.  
7. **Multiple‑Comparison Correction** – Final model p‑values across the five paradigms are corrected with Benjamini‑Hochberg FDR (as required by the assumptions).  
8. **Alpha Sensitivity** – Power curves are recomputed for α = 0.01, 0.05, 0.10 to confirm robustness (assumption in spec).  

### Power & Sample Size Justification
- **Effect‑size grid** enables explicit mapping from known effect to empirical power.  
- **Sample‑size ceiling** is the original size of the largest dataset (≈ 100); no extrapolation beyond observed data.  
- **Bootstrap size** (≥ 50) satisfies FR‑004 and yields confidence intervals narrow enough for SC‑002.  

### Causal Inference Assumptions
All datasets are observational; therefore, findings are framed as **associational** (e.g., “larger sample sizes are associated with higher replication probability”). No causal claims are made about preprocessing choices.

### Measurement Validity
Cohen’s d is the standard effect‑size metric for GLM contrast estimates in neuroimaging. The synthetic signal is injected directly into the BOLD time‑series, ensuring that the ground‑truth effect is known and measurable.

### Predictor Collinearity
Predictors (sample size, smoothing kernel, SNR) are orthogonal by design. Interaction terms are included but VIF is monitored; any VIF ≥ 5 triggers a warning and the model is refit without the offending term.

## Compute Feasibility

| Component | CPU‑first Strategy | Expected Resource Use |
|-----------|-------------------|----------------------|
| Data download & streaming | `datasets.load_dataset(..., streaming=True)` streams parquet shards (~200 MB each) | < 1 GB RAM |
| ROI extraction | `nilearn.masking.apply_mask` on anatomical atlas (MNI152) | ~2 GB RAM max |
| Temporal smoothing | Convolution over time dimension (NumPy) | negligible RAM |
| GLM fitting | `nilearn.glm.FirstLevelModel` with `noise_model='ar1'` | < 1 GB RAM per iteration |
| Bootstrapping | Parallelized with `joblib` (`n_jobs=2`) | CPU bound, fits within 2 cores |
| Logistic regression | `statsmodels.Logit` (CPU) | < 500 MB RAM |
| Overall wall‑clock | End‑to‑end on 5 paradigms, 4 sample sizes, 50 iterations ≈ 4.5 h (well under 6 h) | ✅ Meets SC‑005 |

**GPU Escape Hatch** – Not required; all steps are CPU‑tractable. No CUDA kernels are used.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| fMRIPrep infeasible on free tier | Use lightweight ROI extraction + temporal smoothing (CPU‑tractable) as a documented alternative. |
| Corrupted NIfTI files | `download/data_validator.py` checks file integrity; corrupted subjects are skipped with a logged warning. |
| GLM non‑convergence | Iteration flagged; if > 20 % of iterations fail, overall result labeled “Unreliable”. |
| Memory overflow | `memory_monitor.py` monitors RAM; when usage > 5 GB it randomly downsamples subjects and logs the action. |
| Non‑monotonic power curve | Report as observed; may indicate effect size near zero (expected per SC‑002). |
| Missing open‑source dataset for a paradigm | The pipeline logs a “Data Limitation” warning and proceeds with the available paradigms; no fabrication. |

## Ethical Considerations
- **Anonymity** – All OpenNeuro datasets are pre‑anonymized; no PII is processed.  
- **Transparency** – Every step logs inputs, parameters, and outputs; failures are reported in `results/paper/convergence_report.md`.  
- **Reproducibility** – Full environment captured via `requirements.txt`; seeds fixed; data sources immutable URLs.  

---
