# Research: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Dataset Strategy

### 1.1 Verified Sources Analysis
The specification requires rs‑fMRI data with a reliable musical‑training variable. The verified dataset list contains **no** open source that satisfies both requirements:

| Dataset | Verified? | Reason |
|---------|-----------|--------|
| **ABCD** | ❌ (URLs point to unrelated zip files) | No rs‑fMRI + training metadata. |
| **HCP‑Adolescents** | ❌ (explicitly “NO verified source”) | Missing required variables. |
| **HCP (parquet)** | ❌ (diffusion‑only) | Not rs‑fMRI and no training data. |
| **MNI / ROI / SES** | ❌ (no verified source) | Not suitable for the primary analysis. |

**Conclusion**: No open, programmatically downloadable dataset meets **FR‑001**. Consequently the pipeline runs in **Synthetic Verification Mode** by default. When a verified dataset becomes available, the same code can be invoked with `--mode real --data-path <path>`.

### 1.2 Synthetic Data Fit
The synthetic generator creates a fully compliant dataset for **pipeline verification** (not for scientific inference):

| Variable | Source | Distribution (synthetic) |
|----------|--------|--------------------------|
| `subject_id` | UUID‑like string | Uniform |
| `group` | Derived from `years_of_training` | `"musician"` if `years_of_training ≥ 1`; otherwise `"non_musician"` |
| `years_of_training` | Uniform 1–10 yr for musicians; 0 for non‑musicians | Continuous |
| `age` | Normal (15 ± 1 yr) | Continuous |
| `sex` | 50/50 split | Categorical |
| `motion_score` | Normal (0.15 ± 0.05) | Continuous |
| `ses_score` | Normal (0 ± 1) | Continuous |
| `rs_fmri_path` | Mock NIfTI path | Generated Gaussian noise volume |
| Optional **effect injection** | Parameter `--inject-effect` (disabled by default) | Adds a modest group effect (Cohen’s d ≈ 0.4) **only for power‑simulation**, not for primary analysis. |

All synthetic artifacts conform to the JSON‑Schema contracts in `contracts/`. A **stress‑test** variant can inject a known effect to confirm detection power, but the default run contains **no systematic group differences**, providing an unbiased verification of false‑positive control.

### 1.3 Variable Mapping
The pipeline expects the following exact column names in the subject table:

- `subject_id`
- `group`
- `years_of_training`
- `age`
- `sex`
- `motion_score`
- `ses_score`
- `rs_fmri_path` (path to the mock NIfTI)

Missing columns cause an explicit abort with a clear error message.

## 2. Statistical Methodology

### 2.1 Group Comparison (FR‑003)
- **Test**: Welch’s t‑test (unequal variances) per edge.  
- **Multiple‑Comparison**: **Benjamini‑Yekutieli (BY) FDR** (α = 0.05), appropriate for dependent edge tests.  
- **Effect Size**: Cohen’s d; 95 % CI via 1 000 bootstrap resamples.  

### 2.2 Network‑Based Statistic (FR‑008)
1. Threshold t‑statistics at **t = 1.8, 2.0, 2.5** (≈ uncorrected p ≈ 0.07, 0.05, 0.03).  
2. Identify connected components with `networkx`.  
3. Permute group labels repeatedly, recompute component sizes, build null distribution.  
4. Compute family‑wise error‑corrected p‑value for the largest observed component.  

Reporting results across three thresholds provides a built‑in sensitivity check.

### 2.3 Correlation Analysis (FR‑004)
- **Metric**: Pearson r (Spearman if Shapiro‑Wilk rejects normality).  
- **Scope**: Musicians only (`group == "musician"`).  
- **Multiple‑Testing**: **BY FDR** across all edges.  
- **Outputs**: r, two‑tailed p, **R²**, 95 % CI (Fisher‑z), BY‑corrected q‑value.

### 2.4 Sensitivity Analysis (FR‑005)
- **Thresholds**: q = 0.01, 0.05, 0.10 (FDR‑corrected).  
- **Outcome**: Table of significant edge counts per threshold; percentage change between q = 0.05 and q = 0.01; flag “low stability” if count drops > 30 % or if the 95 % CI for R² includes zero at the stricter threshold.

### 2.5 Confound Handling (FR‑009)
- **Primary**: Propensity‑score matching (nearest‑neighbor, caliper = 0.2 SD) on age, sex, motion, SES.  
- **Fallback**: Regression residualization of each edge on the same covariates, applied regardless of matching outcome.  
- **Diagnostics**: Standardized mean differences (SMD) < 0.1 required; if not achieved, a warning is logged but analysis proceeds with residualized data.

### 2.6 Power & Sample‑Size (SC‑005)
- Simulate a substantial number of synthetic datasets with a known medium effect.  
- Run the full BY‑corrected pipeline on each.  
- Estimate detection rate → post‑hoc power estimate logged in `research.md`.  
- If either group falls below **50** subjects after filtering, the pipeline aborts with “Sample Size Insufficient” (per US‑1).

### 2.7 Causal Framing
Observational design → all findings are reported as **associational** (e.g., “musical training is associated with stronger connectivity”).

## 3. Computational Feasibility

- **Memory**: Each 200 × 200 z‑matrix ≈ 0.32 MB; streaming NIfTI loading ensures peak RAM ≤ 2 GB for synthetic data; memory monitor aborts > 7 GB.  
- **Runtime** (empirical on a 2‑core GitHub runner):  
  - Synthetic generation ≈ seconds.  
  - Connectivity computation ≈ few minutes.  
  - Welch’s tests ≈ seconds.  
  - NBS (a large number of permutations × multiple thresholds) requires on the order of a few hours when vectorized.  
  - Correlation & sensitivity ≈ minutes.  
  **Total < 4 h**, comfortably within the 6 h limit.  
- **GPU**: Not required; all libraries are CPU‑compatible.

## 4. Decision Log

| Decision | Rationale |
|----------|-----------|
| Keep musician definition at **≥ 1 year** | Aligns with specification (FR‑001) and literature precedent; avoids arbitrary tightening. |
| Default to **Synthetic Verification Mode** | No open dataset satisfies FR‑001; synthetic data validates pipeline without fabricating unavailable data. |
| Implement **dual confound strategy** (matching + residualization) | Guarantees covariate control even if matching discards subjects. |
| Run **NBS at three thresholds** | Provides sensitivity insight and avoids cherry‑picking a single cutoff. |
| Abort on **< 50 subjects per group** | Enforces power assumptions defined in SC‑005. |
| Report all findings as **associational** | Observational data precludes causal claims. |

---

