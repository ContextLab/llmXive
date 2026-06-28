# Research: Bayesian Hierarchical Modeling of Misinformation Cascade Size

## Overview

This research plan outlines the statistical methodology and data strategy for modeling misinformation cascade sizes using Bayesian hierarchical models. The approach prioritizes CPU feasibility, statistical rigor, and adherence to the project constitution.

## Dataset Strategy

The following table maps data requirements to verified sources. **CRITICAL**: The specific PolitiFact and SNAP Twitter cascade datasets mentioned in the Spec's Assumptions **do not have verified sources** in the provided `Verified datasets` block. The pipeline is designed to accept user-supplied local data (JSON only) to satisfy FR-001, while using available dummy data for schema validation only.

| Requirement | Dataset Source | Verified URL | Status |
|:--- |:--- |:--- |:--- |
| **FR-001** (Raw Cascade) | User-supplied Local Data | **NO verified source found** | ⚠️ **Gap**: Pipeline must accept local JSON edge-list. |
| **FR-003** (Susceptibility) | Historical Activity Metrics | **NO verified source found** | ⚠️ **Gap**: Proxy computation required if missing. |
| **SC-004** (Runtime Benchmark) | Benchmark Dataset | **NO verified source found** | ⚠️ **Gap**: Synthetic generator required. |
| **Schema Test** | Dummy CSV | ` | ✅ Used for schema validation only. |
| **SNAP Reference** | SNAP Stark | ` | ⚠️ Not cascade topology; Q&A only. |

**Rationale**: Since no verified misinformation cascade topology dataset is available in the provided list, the implementation must rely on the `FR-001` specification to ingest *any* valid JSON edge-list. The benchmark execution (US-1) will require the researcher to supply a valid cascade file locally or use a synthetic data generator (code-generated) that adheres to the schema.

**Spec-Root Cause Flag**: Spec Assumptions state public datasets contain necessary variables, but research confirms NO verified sources exist. This contradiction requires spec.md Assumptions section update.

## Methodology & Statistical Rigor

### Model Specification

The core model is a Bayesian Hierarchical Negative Binomial Model (count outcome):

$$ \text{CascadeSize}_i \sim \text{NegBinomial}(\mu_i, \phi) $$
$$ \log(\mu_i) = \beta_0 + \beta_{network} X_{network, i} + \beta_{user} X_{user, i} + u_{user[i]} + u_{message[i]} $$

- **Fixed Effects**: Pre-cascade network context features (NOT cascade topology to avoid circularity), User activity proxy score.
- **Random Effects**: User ID, Message ID. If multiple platforms exist, Platform ID is added as a random intercept (FR-004 Clarification).
- **Priors**: Weakly informative Normal(0, 10) for fixed effects; Half-Cauchy for scale parameters; Gamma for dispersion.
- **Inference**: HMC/NUTS via `numpyro` (CPU-compatible).
- **Likelihood Choice**: Negative Binomial selected over Normal because cascade size is count data (non-negative integers, typically skewed).

### Statistical Controls

- **Multiple Comparisons**: Family-wise error rate controlled via Bayesian credible intervals (SC-001). No p-values; focus on posterior probability of non-zero effect.
- **Sample Size/Power**: Minimum thresholds for hierarchical model stability:
 - Minimum 30 users (random effect level)
 - Minimum 50 messages (random effect level)
 - Minimum 100 cascades (total observations)
 - *Reference*: Gelman et al. (2020) on hierarchical model requirements.
 - **Note**: If benchmark dataset has fewer observations, power limitation must be explicitly acknowledged in paper.
- **Causal Claims**: Observational data implies associational findings only. No causal claims made without randomization strategy.
- **Collinearity**: VIF computed for all predictors. Pairs with |r| > 0.8 flagged (SC-005). Independent effects not claimed for collinear variables.
- **Model Comparison**: WAIC/LOO-CV used to compare Hierarchical Model vs. Baseline Linear Regression (SC-003).

### Cross-Validation Strategy

**Leave-One-User-Out CV (LOUOCV)** is required instead of k-fold to prevent information leakage across hierarchical levels:
- Each fold holds out all cascades from one user
- Model trained on remaining users
- Prevents user-level random effects from leaking into test set
- Reference: Standard practice for hierarchical model evaluation

### Compute Feasibility

- **Hardware**: 2 CPU cores, 7 GB RAM (GitHub Actions Free Tier).
- **Library**: `numpyro` (default precision), `networkx` (CPU), `pandas`.
- **Constraints**:
 - No GPU/CUDA.
 - No 8-bit/4-bit quantization.
 - Data subset to fit RAM (cascades > 2,000 nodes skipped; reduced from [deferred] spec limit for CPU feasibility).
 - Runtime capped at a predetermined duration.
 - Memory profiling step added to validate [deferred] node limit empirically during Phase 0.

**Spec-Root Cause Flag**: Spec Assumptions state [deferred] node limit but this exceeds CPU feasibility. Plan reduces to [deferred] nodes. **SPEC ROOT CAUSE - FLAGGED FOR KICKBACK**

## Risk Mitigation

1. **Dataset Gap**: If no local cascade data is provided, the pipeline will fail at FR-001. Mitigation: Provide a synthetic data generator script in `code/` for testing purposes.
2. **Convergence**: If HMC diverges > 5%, reduce step size automatically (Edge Case). If still failing, exit with diagnostic.
3. **Memory**: Monitor RSS; abort if > 7 GB (FR-008). Empirical validation of [deferred] node limit during Phase 0.
4. **Construct Validity**: User-susceptibility proxy measures activity level, not true susceptibility. This limitation must be explicitly acknowledged in paper; consider renaming to "activity_level_proxy" in documentation.
5. **Circular Validation**: Network features derived from pre-cascade context, NOT cascade topology, to avoid outcome dependence. **Spec FR-002 Contradiction**: FR-002 requires cascade depth feature but this creates circular validation. Implementation uses pre-cascade context instead. **SPEC ROOT CAUSE - FLAGGED FOR KICKBACK**

## Construct Validity Notes

**User Susceptibility Proxy**: The proxy (degree ≥ 2, shares ≥ 1) measures historical activity level, not susceptibility to misinformation. This is a construct validity limitation. The documentation (`susceptibility_method.md`) must clarify this distinction. A validated susceptibility metric would require different data (e.g., psychological assessments, exposure-response data) not available in current datasets.

**Network Features**: Features computed from user's pre-cascade network context (historical degree, clustering in broader network) rather than cascade topology itself, to avoid circular validation where predictors are mathematically dependent on the outcome variable.