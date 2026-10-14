# Research: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Dataset Strategy

### 1.1 Verified Sources Analysis
The specification requires adolescent rs-fMRI plus a reliable musical-training variable. The verified dataset block contains **no** open source satisfying both:

| Dataset | Verified? | Reason |
|---------|-----------|--------|
| ABCD (zip) | ❌ | The two verified URLs are unrelated zip archives; they do not contain ABCD rs-fMRI or training metadata. ABCD proper is access-gated (NDA data-use agreement) and cannot be fetched by the CI runner. |
| HCP-Adolescents | ❌ | No verified source found; HCP-D is access-gated. |
| HCP (parquet) | ❌ | Verified URLs are diffusion/behavioral tabular data — no rs-fMRI, no musical-training variable. |
| MNI (parquet) | ❌ | The verified URLs are MNIST/Fashion-MNIST image datasets — unrelated despite the name overlap. |
| ROI / SES / ConnectivityMatrix | ❌ | No verified source found. |

**Conclusion**: No open, programmatically downloadable dataset meets FR-001. Per the data-availability rules, we do NOT plan as if ABCD/HCP-D were downloadable, and we do NOT fabricate a mirror. The pipeline therefore defaults to **Synthetic Verification Mode** (pipeline validation only, no scientific claims), with a `--mode real` path ready for a future verified dataset. This is an explicit scope limitation, surfaced for spec revision, not silently resolved.

**Re-plan trigger (testable)**: the deferred real-data mode (FR-001 real clause and FR-011 real-data validation) activates when a named dataset passes the verified-dataset gate — a reachable, programmatically downloadable source confirmed by the Reference-Validator Agent — that contains adolescent rs-fMRI, a musical-training variable, and the confounder columns (age, sex, motion, SES) per the Subject schema.

### 1.2 Synthetic Data Specification (verification only)
| Variable | Distribution |
|----------|--------------|
| `subject_id` | UUID-like string |
| `group` | `"musician"` ⇔ `years_of_training ≥ 1` |
| `years_of_training` | Uniform(1,10) musicians; 0 non-musicians |
| `age` | Normal(15, 1) |
| `sex` | 50/50 M/F |
| `motion_score` | Normal(0.15, 0.05), clipped ≥ 0 |
| `ses_score` | Normal(0, 1) |
| `rs_fmri_path` | Mock 64³ Gaussian-noise NIfTI |
| Effect injection | **Disabled by default**; `--inject-effect` (d≈0.4) used only in the power simulation |
| Quality defects | Seeded injection of missing training-history values and corrupted NIfTI files, so exclusion logic and the SC-005 audit have a genuine failure mode to detect |

Default run has no systematic group difference → unbiased verification of false-positive control (FR-011: synthetic effect injection is NOT used for scientific validation).

### 1.3 Variable Mapping
Exact required columns: `subject_id`, `group`, `years_of_training`, `age`, `sex`, `motion_score`, `ses_score`, `rs_fmri_path`. Missing columns → explicit abort.

## 2. Statistical Methodology

### 2.1 Group Comparison (FR-003)
- Welch's t-test per edge within auditory, motor, executive networks.
- **Benjamini-Hochberg FDR** (as specified) at α = 0.05. (BY was considered for edge dependence; the spec names BH, so BH is used and edge dependence acknowledged as a limitation.)
- Cohen's d; 95% CI via bootstrap (1000 resamples).
- **NetworkMetric aggregation**: per-subject mean within-network connectivity (auditory/motor/executive) is computed from the z-matrices and carried into the results summary, per the spec's Key Entities.

### 2.2 Network-Based Statistic (FR-008)
Threshold t ∈ {1.8, 2.0, 2.5}; connected components via `networkx`; group-label permutation (1000) builds the null; FWER-corrected p for the largest component. Three thresholds give a built-in sensitivity check.

### 2.3 Correlation (FR-004)
Musicians only; Pearson (Spearman if Shapiro-Wilk rejects normality); BH FDR across edges; r, p, q, effect size, 95% CI (Fisher-z).

### 2.4 Sensitivity (FR-005)
q ∈ {0.01, 0.05, 0.10}; count table; percentage reduction 0.05→0.01; "low stability" flag when CI includes zero at the stricter threshold.

### 2.5 Confounds (FR-009)
Propensity matching (nearest-neighbor, caliper 0.2 SD) on age/sex/motion/SES defines the analysis sample; edge-wise linear residualization is then applied to the matched sample for additional covariate adjustment. Ordering note: the matched sample is a subset of the full cohort, and residualization is applied to that matched sample (not the full set), so the estimand is the matched-sample group difference with covariate adjustment; SMD diagnostics (<0.1 target, warning otherwise) are reported on the matched sample before residualization.

### 2.6 Power (SC-005 context)
Spec assumption: 50–75/group detects d≈0.5 at power ≥0.80 — acknowledged as an assumption, not established. Power simulation on effect-injected synthetic data provides a detection-rate estimate; the observational, synthetic-verification framing means no causal or empirical claim is made from these runs.

### 2.7 Causal Framing
Observational design → associational language only. (In the current synthetic mode, no scientific claim is made at all.)

### 2.8 Reviewer concern: musician cutoff
The ≥1-year cutoff is spec-fixed. Literature on musician brains typically studies multi-year, currently-practicing musicians; a 1-year cutoff may dilute effects toward the null. The plan keeps the spec's cutoff, reports the within-musician training-duration distribution, and flags the cutoff as a candidate spec revision.

## 3. Computational Feasibility (CPU-first)
- **CPU choice**: all methods (Pearson correlation, Welch's t, FDR, permutation NBS, bootstrap) are classical statistics with faithful CPU forms. No GPU escape hatch needed.
- **Memory (FR-006 adaptive fallback)**: 200×200 z-matrix ≈ 0.32 MB/subject; per-subject streaming keeps peak RAM well under 7 GB. If a step still approaches the limit, the monitor applies deterministic seeded subsetting before any abort; abort is a last resort only.
- **Runtime**: generation seconds; connectivity minutes; t-tests seconds; NBS (1000 permutations × 3 thresholds, vectorized) a few hours; total < 6 h on a 2-core runner.
- **GPU**: none required; nothing is offloaded to Kaggle.

## 4. Decision Log
| Decision | Rationale |
|----------|-----------|
| Keep ≥1-year musician definition | Spec-fixed (FR-001); flagged as possible future revision per reviewer feedback; training-duration distribution reported. |
| Synthetic Verification Mode default | No verified open dataset satisfies FR-001; refuses to fabricate data or fake mirrors. |
| FR-011 real-data clause explicitly DEFERRED | No real data exists; synthetic-null permutation runs validate machinery only. Real-data validation activates under the same testable re-plan trigger as FR-001. |
| Testable re-plan trigger | A named dataset passing the verified-dataset gate with adolescent rs-fMRI + a training variable + confounders. |
| Inject synthetic quality defects | Gives the SC-005 inclusion audit and exclusion logic a genuine failure mode; clean-fraction assertion remains scientifically meaningful only in real-data mode. |
| Add NetworkMetric entity + aggregation step | Spec Key Entity previously had no producing step; now computed per subject and schema-validated. |
| Adaptive memory fallback before abort | FR-006 mandates sampling/subsetting, not abort; streaming + deterministic subsetting implemented first. |
| BH (not BY) FDR | Spec names Benjamini-Hochberg; edge dependence noted as limitation. |
| Dual confound strategy with stated ordering | Matching defines the sample (estimand: matched-sample difference); residualization adjusts within it. |
| NBS at three thresholds | Sensitivity without cherry-picking. |
| Abort <50/group with "Sample Size Insufficient" | Spec edge-case-3 string; both spec phrasings logged; spec inconsistency flagged. |
| Associational framing | No randomization; and currently no real-data claims at all. |
| Repair-first Phase 0 | Verifier-rejected tasks T001–T003, T111: fix the four failing entry points before any new work. |