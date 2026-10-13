# Research: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Dataset Strategy

### 1.1 Verified Sources Analysis
The specification requires ABCD or HCP‑Adolescents data. The provided “Verified datasets” block contains **no** URL that supplies both resting‑state fMRI and a reliable musical‑training variable.

| Dataset | Verified? | Reason |
|---------|-----------|--------|
| **ABCD** | ❌ (URLs point to unrelated zip files) | No rs‑fMRI + training metadata. |
| **HCP‑Adolescents** | ❌ (explicitly “NO verified source”) | Missing required variables. |
| **HCP (general)** | ❌ (diffusion‑only) | Not rs‑fMRI and no training data. |
| **MNI / ROI / SES** | ❌ (no verified source) | Needed for spatial normalization or covariates. |

**Conclusion**: No open, programmatically downloadable dataset satisfies **FR‑001**. Consequently the pipeline will operate in **Synthetic Verification Mode** by default. When a verified dataset becomes available, the same code can be invoked with `--mode real --data‑path <path>`.

### 1.2 Synthetic Data Fit
The synthetic generator creates:

| Variable | Source | Distribution (synthetic) |
|----------|--------|--------------------------|
| `subject_id` | UUID‑like string | Uniform |
| `group` | Determined by `years_of_training` | A group of musicians and a matched group of non‑musicians. |
| `years_of_training` | Uniform 1–10 yr for musicians; 0 for non‑musicians | Continuous |
| `age` | Normal (15 ± 1 yr) | Continuous |
| `sex` | 50/50 split | Categorical |
| `motion_score` | Normal (0.15 ± 0.05) | Continuous |
| `ses_score` | Normal (0 ± 1) | Continuous |
| `connectivity` | Multivariate Gaussian with mean 0, covariance ≈ 0.2, **no group effect** (null‑first) | Z‑transformed matrices |

The synthetic data respects all schema constraints (see `contracts/`). A **stress‑test** variant can inject a modest group effect (Cohen’s d ≈ moderate effect size) to verify detection pipelines.

### 1.3 Variable Mapping
All required variables are present in the synthetic tables. For real data, the pipeline expects columns named exactly:

- `subject_id`
- `group` (derived from `years_of_training`)
- `years_of_training`
- `age`
- `sex`
- `motion_score`
- `ses_score`
- `rs_fmri_path` (path to NIfTI)

Missing columns cause an explicit abort with a clear error message.

## 2. Statistical Methodology

### 2.1 Group Comparison (FR‑003)
- **Test**: Welch’s t‑test (unequal variances) per edge.  
- **Multiple‑Comparison**: **Benjamini‑Yekutieli (BY) FDR** (α = 0.05), which accounts for dependence among edges.  
- **Effect Size**: Cohen’s d with pooled SD; 95 % CI via 1 000 bootstrap resamples.  
- **Rationale**: BY is conservative for dependent tests, reducing false‑positive inflation inherent in edge‑wise analyses.

### 2.2 Network‑Based Statistic (FR‑008)
- **Procedure**:  
  1. Threshold t‑statistics at three primary values (t = 1.8, 2.0, 2.5) corresponding roughly to uncorrected p ≈ 0.07, 0.05, 0.03.  
  2. Identify connected components with `networkx`.  
  3. Permute group labels 1 000 times, recompute component sizes, build null distribution.  
  4. Compute family‑wise error‑corrected p‑value for the largest observed component.  
- **Justification**: Reporting results across multiple thresholds provides sensitivity analysis and avoids cherry‑picking a single arbitrary threshold.

### 2.3 Correlation Analysis (FR‑004)
- **Metric**: Pearson r (Spearman if Shapiro‑Wilk rejects normality).  
- **Scope**: Only subjects with `group == "musician"`.  
- **Multiple‑Testing**: **BY FDR** applied across all edges.  
- **Outputs**: r, two‑tailed p, **R²** (coefficient of determination) as an effect size, 95 % CI (Fisher‑z), and BY‑corrected q‑value.

### 2.4 Sensitivity Analysis (FR‑005)
- **Thresholds**: q = 0.01, 0.05, 0.10 (FDR‑corrected).  
- **Outcome**: Table of significant edge counts per threshold; percentage change between q = 0.05 and q = 0.01; flag “low stability” if count drops > 30 % or if the 95 % CI for R² includes zero at the stricter threshold.

### 2.5 Confound Handling (FR‑009)
- **Primary**: Propensity‑score matching (nearest‑neighbor, caliper = 0.2 SD) on age, sex, motion, SES.  
- **Unconditional Fallback**: Regardless of matching success, **regression residualization** of each edge on the same covariates is always performed before any testing.  
- **Diagnostics**: Post‑matching standardized mean differences (SMD) < 0.1 required; if not achieved, a warning is logged but analysis proceeds with residualized data.

### 2.6 Power & Sample‑Size (SC‑005)
- **Assumption**: 50–75 subjects per group → ≥ 0.80 power for medium effects (d ≈ 0.5) **when accounting for BY‑corrected edge‑wise testing** is optimistic.  
- **Implementation**: A **simulation‑based power analysis** will generate A substantial set of synthetic datasets. with a known effect size, run the full BY‑corrected pipeline, and estimate detection rate. The post‑hoc power estimate is logged in `research.md`.  
- **If < 50 per group**: Pipeline halts with “Sample Size Insufficient” (per US‑1).

### 2.7 Causal Framing
Observational design → results reported as **associational** (e.g., “musical training is associated with stronger connectivity”).

## 3. Computational Feasibility

- **Memory**: Each 200 × 200 z‑matrix ≈ 0.32 MB; A large set of matrices of substantial size (on the order of tens of megabytes).. Streaming NIfTI files one‑by‑one ensures ≤ 2 GB peak RAM. `memory_monitor.py` aborts if > 7 GB.  
- **Runtime** (empirical on a Multi‑core GitHub runner):  
  - Synthetic generation ≈ short duration (on the order of seconds)  
  - Connectivity computation ≈ a few minutes  
  - Welch’s tests ≈ a brief duration.  
  - NBS (a large number of permutations × 3 thresholds) ≈ several hours (vectorized)  
  - Correlation & sensitivity ≈ a short duration.  
  **Total < 4 h**, within the designated time limit.  
- **GPU**: Not required; all libraries are CPU‑compatible.

## 4. Decision Log

| Decision | Rationale |
|----------|-----------|
| Use **built‑in atlas CSV** instead of downloading | Guarantees deterministic availability on CI. |
| Default to **synthetic verification mode** | No verified open dataset satisfies FR‑001; synthetic data enables end‑to‑end testing without fabricating unavailable data. |
| Implement **dual confound strategy** (matching + residualization) | Prevents bias if matching discards too many subjects; ensures all analyses adjust for covariates. |
| Run **NBS at three thresholds** | Provides sensitivity insight and avoids a single arbitrary cutoff. |
| Abort on **< 50 subjects per group** | Enforces power assumption defined in US‑1 and SC‑005. |
| Report all findings as **associational** | Observational data precludes causal claims. |

---

