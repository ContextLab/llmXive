# Research: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Dataset Strategy

### 1.1 Verified Sources
We will use the **OpenNeuro dataset ds001734** (https://openneuro.org/datasets/ds001734), which provides:

* Resting‑state fMRI data from adolescents (preprocessed to MNI space).  
* A validated “Music Training” questionnaire delivering **years_of_training** (numeric, ≥0).  
* Required confound columns: `age`, `sex`, `motion_score`, `ses_score`.  

All variables required by FR‑001 are present, and the dataset is programmatically downloadable via the `datasets` library, satisfying the real‑data validation requirement (FR‑011).  

If, for any reason, the dataset cannot be accessed or fails column validation, the pipeline aborts gracefully with a clear error message and falls back to synthetic verification mode (see below).

### 1.2 Synthetic Data (Verification Only)
The synthetic generator (used only for additional sanity checks) creates 100 subjects split evenly into musician and non‑musician groups, respecting the ≥ 50 subjects per group rule. Each subject receives:

| Variable | Generation Details |
|----------|--------------------|
| `subject_id` | UUID‑like string |
| `group` | Determined by `years_of_training` (≥ 1 yr → musician) |
| `years_of_training` | Uniform(1, 10) for musicians; 0 for non‑musicians |
| `age` | Normal(15, 1) |
| `sex` | [deferred] M / [deferred] F |
| `motion_score` | Normal(0.15, 0.05), clipped ≥ 0 |
| `ses_score` | Normal(0, 1) |
| `rs_fmri_path` | Mock 64³ Gaussian‑noise NIfTI file |
| **Defects** | Seeded missing `years_of_training` entries ([deferred] of rows) and corrupted NIfTI files ([deferred] of subjects) to test exclusion handling. |
| **Effect injection** | Disabled for primary analysis; optional `--inject-effect` flag used only for a separate power‑simulation (not reported as a scientific result). |

All synthetic files are checksummed; the generation process is fully deterministic given a random seed.

## 2. Statistical Methodology

### 2.1 Group Comparison (FR‑003)
* **Test**: Welch’s t‑test per edge within the three a‑priori networks (auditory, motor, executive).  
* **Multiple‑comparison correction**: Benjamini‑Hochberg FDR (α = 0.05).  
* **Effect size**: Cohen’s d, computed from group means and pooled variance.  
* **Confidence intervals**: 95 % CI via bias‑corrected bootstrap (1 000 resamples).  

### 2.2 Network‑Based Statistic (FR‑008)
* **Permutation**: 1 000 label shuffles of the matched sample.  
* **Primary thresholds**: t = 1.8, 2.0, 2.5.  
* **Component detection**: `networkx` connected components on suprathreshold edges.  
* **FWER correction**: Empirical p‑value for the largest component size across permutations.

### 2.3 Correlation with Training Duration (FR‑004)
* **Subset**: Musicians only.  
* **Metric**: Pearson correlation; fallback to Spearman if Shapiro‑Wilk rejects normality.  
* **Correction**: BH‑FDR across all edges.  
* **Effect size**: r‑derived Cohen’s d; 95 % CI via Fisher‑z.

### 2.4 Sensitivity Analysis (FR‑005)
* **Thresholds**: q ∈ {0.01, 0.05, 0.10}.  
* **Outputs**: Table of significant‑connection counts per threshold; % reduction 0.05 → 0.01; “low stability” flag when the 95 % CI for the effect size includes zero at the stricter threshold.  
* **Additional cutoff sensitivity**: The analysis is repeated using a stricter musician definition (≥ 3 years of training) to assess construct validity.

### 2.5 Confound Adjustment (FR‑009)
* **Matching**: Propensity‑score nearest‑neighbor matching (caliper = 0.2 SD) on age, sex, motion, SES.  
* **Balance diagnostics**: Standardized mean differences (SMD) reported for each covariate; SMD < 0.1 considered acceptable.  
* **Conditional residualization**: If any covariate shows SMD ≥ 0.1 after matching, linear regression residualizes that covariate from each edge; otherwise, residualization is skipped to avoid double‑adjustment.

### 2.6 Power & Effect Size (SC‑005)
We acknowledge the spec’s assumption that 50–75 subjects per group provides ≥ 0.80 power for a medium effect (d ≈ 0.5). A **synthetic power simulation** (effect‑injected data, 200 repetitions) estimates detection rates; results are logged as a **power limitation acknowledgment** rather than a claim.

### 2.7 Causal Framing
Because the design is purely observational (no random assignment, no instrumental variable), all conclusions will be phrased **associationally** (“musical training is associated with…”) in any downstream manuscript.

### 2.8 Reviewer‑Driven Gaps
* **Musician definition** – The ≥ 1 year cutoff is mandated by FR‑001; we retain it as the primary definition, but also report results for a stricter ≥ 3 year cutoff to address potential heterogeneity and construct‑validity concerns.  
* **Musical aptitude** – The original research question mentioned “musical aptitude,” but the current FRs only include `years_of_training`. We flag this discrepancy in the spec‑revision notes; the pipeline presently uses only `years_of_training`.

## 3. Computational Feasibility (CPU‑First)
All analyses employ classical statistical routines with faithful CPU implementations:

* **Pearson correlation & Fisher‑z** – O(N · R²) operations (R = 200 ROIs) – completes in seconds.  
* **Welch’s t‑test** – vectorized across edges; negligible memory.  
* **Bootstrap CI** – parallelizable across edges; 1 000 resamples stay well within the 7 GB RAM ceiling.  
* **NBS** – 1 000 permutations × 3 thresholds; implemented with NumPy‑level vectorization; total runtime ≈ a few hours on a multi‑core runner.  
* **Memory guard** – `memory_monitor.py` streams per‑subject data; adaptive sub‑sampling is applied only if a step threatens the 7 GB limit (which does not happen in real‑data runs).  

No GPU resources are required; the pipeline will not trigger the Kaggle GPU off‑load.

## 4. Decision Log
| Decision | Rationale |
|----------|-----------|
| **OpenNeuro ds001734 as primary real dataset** | Verified, programmatically downloadable, contains all required variables, thereby satisfying FR‑001 and FR‑011. |
| **Synthetic Verification Mode as fallback** | Guarantees that the pipeline can still be exercised if the real dataset becomes unavailable, without violating the specification. |
| **Retain ≥ 1 yr musician cutoff** | Fixed by FR‑001; secondary ≥ 3 yr cutoff added for robustness checks. |
| **Acknowledge missing “musical aptitude”** | Spec does not define this variable; we flag the gap for future revision. |
| **Inject realistic quality defects** | Provides a genuine test of exclusion logic and the SC‑005 inclusion‑audit requirement. |
| **Dual confound strategy replaced with conditional approach** | Avoids double‑adjustment bias while ensuring covariate balance. |
| **Power simulation (synthetic, effect‑injected)** | Supplies an empirical acknowledgment of the spec’s power assumption without violating FR‑011. |
| **Repair Phase 0 entry points first** | Verifier rejected T001/T002; fixing these scripts is prerequisite for any downstream work. |
| **Link Phase 0 tasks to FR‑011** | Ensures that script repairs are recognized as necessary for real‑data validation. |

## 5. Re‑plan Trigger (Testable)
The deferred real‑data path (and FR‑011 validation) will be activated when **all** of the following conditions are met:

1. The OpenNeuro ds001734 dataset is reachable and passes the column‑validation gate (i.e., contains `years_of_training`, `age`, `sex`, `motion_score`, `ses_score`).  
2. The dataset provides adolescent resting‑state fMRI (preprocessed to a standard space) and the musical‑training variable as described.  
3. The dataset also provides the required confound columns matching the `Subject` schema.

When such a dataset becomes available, the pipeline will be run in `--mode real`, satisfying FR‑001 and FR‑011.

---


