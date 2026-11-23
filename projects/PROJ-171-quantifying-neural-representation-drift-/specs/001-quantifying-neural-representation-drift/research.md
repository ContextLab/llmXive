# Research: Quantifying Neural Representation Drift During Skill Learning

## Summary
The research tests whether the **exponential drift rate** `b` (from `drift(t)=a·exp(−b·t)+c`) predicts individual learning speed during motor skill acquisition, as mandated by Constitution VII. To satisfy the functional requirements of the MVP (FR-005), the **linear drift rate** (from `drift(t)=a+b·t`) is also computed and reported. The analysis runs entirely on a CPU‑only GitHub Actions runner.

## Dataset Strategy

| Dataset | Verified URL | Variables Present | Role |
|---|---|---|---|
| **Synthetic Ground Truth** | *Generated locally* (no external URL) | `spike_counts`, `trial_success`, `subject_id`, `day_index` | Primary source for MVP; provides known drift parameters for SC‑001 validation and ensures correct neural modality. |

### Data Access & Streaming
- Synthetic data are generated on‑the‑fly by `src.validation.synthetic` to ensure the dataset contains the specific required variables (`spike_counts`, `trial_success`) which are often missing or improperly formatted in open-access repositories.
- Checksums are recorded in `data/raw/checksums.txt` (Constitution III).

## Methodological Rigor

### 1. Drift Quantification
- **Research Primary Model**: Exponential decay fit (`drift(t)=a·exp(−b·t)+c`). The fitted `b` is the main predictor for learning speed (satisfies Constitution VII).  
- **Functional Primary Model**: Linear regression (`drift(t)=a+b·t`) is computed to meet FR‑005 and for synthetic‑data validation (SC‑001).  
- **Permutation Test**: Shuffle day labels 10 000 times; compute null distribution of exponential `b`; report two‑tailed p‑value.  
- **Multiple‑Metric Correction**: If Pearson, Cosine, and Mahalanobis distances are all evaluated, Bonferroni correction is applied (FR‑007).  

### 2. Behavioral Correlation & Hypothesis Testing
- **Learning Speed**: Days to reach a predefined success threshold (interpolated if missing).  
- **Pearson Correlation**: `r` between exponential `b` and learning speed.  
- **Permutation Test**: 10 000 label shuffles → p‑value (SC‑002).  
- **Linear Mixed‑Effects Model**: `learning_speed ~ drift_rate_exp + (1|subject)` using `statsmodels` (FR‑006).  
- **Power Check**: If `N < 15`, `power_warning=True` and a warning is recorded (SC‑005).  

### 3. Robustness & Sensitivity
- **Threshold Sweep**: Stability thresholds {0.70, 0.75, 0.80, 0.85, 0.90}.  
- **Metric Comparison**: Exponential drift rates computed with Pearson, Cosine, Mahalanobis distances; sign of correlation with learning speed must remain consistent (SC‑003).  
- **Split‑Half Reliability**: Randomly split sessions; compute drift rates on each half; report correlation (FR‑008).  
- **Performance‑Modulated Unit Exclusion Sensitivity**: Run with/without exclusion and compare results.  
- **Imputation Sensitivity**: Run with and without linear interpolation of missing behavioral logs.  

### 4. Validation with Synthetic Data
- Generate synthetic population matrices with a known exponential drift parameter `b_gt`.  
- Run the full pipeline; verify recovered `b` is within **[deferred]** of `b_gt` (SC‑001).

## Computational Feasibility
- All analyses use CPU‑compatible libraries (`numpy`, `scipy`, `statsmodels`).  
- Memory usage monitored via `tracemalloc`; peak < 7 GB.  
- Expected total runtime on GitHub Actions free tier: **≈ 4 h** (well under 6 h).  

## Decision Rationale
| Decision | Reason |
|---|---|
| **Dual-Model Approach** | Resolves conflict between Constitution VII (Exponential primary for research) and FR-005 (Linear primary for MVP). |
| **Synthetic dataset primary** | Ensures the presence of spike-sorted neural data and behavioral logs, avoiding the modality mismatches found in available open-access imaging datasets. |
| **Config flag `primary_model`** | Allows researchers to explicitly switch the correlation input between linear and exponential metrics for exploratory analyses. |
| **Threshold sweep range** | Covers the required boundary checks from US‑3 and ensures robustness (SC‑004). |