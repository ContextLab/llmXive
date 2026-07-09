# Research: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Research Question
Does self-compassion (SCS) moderate the relationship between negative feedback and psychological outcomes (anxiety, rumination, self-efficacy)?

## Methodology

### Statistical Approach
The core analysis is a **Moderated ANCOVA** (Analysis of Covariance) for each of the three outcomes:
1.  **Outcome**: Post-feedback score (e.g., `stai_post`).
2.  **Predictor**: Feedback Condition (Categorical: Positive=Ref, Neutral, Negative).
3.  **Moderator**: Self-Compassion (Continuous, z-scored).
4.  **Covariates**: Baseline outcome (e.g., `stai_pre`), Age, Gender, (Big Five traits if present).
5.  **Interaction**: `Feedback_Condition * SCS_z`.

**Model Formula**:
`Outcome_post ~ Feedback_Condition + SCS_z + Feedback_Condition:SCS_z + Baseline_outcome + Age + Gender + [Big_Five]`

### Dataset Strategy

| Dataset Name | Source URL (Verified) | Relevance | Status |
| :--- | :--- | :--- | :--- |
| **Feedback and Self-Compassion** | `https://osf.io/3k9r2/` (Specified in FR-001) | Contains required `stai_post`, `rrs_post`, `gse_post`, `scf_total`, `feedback_cond`. | **UNVERIFIED**. The provided "Verified datasets" block **does not** list a URL for this specific OSF ID. The pipeline will attempt to fetch from the OSF URL. If the file is missing or columns are absent, the pipeline **MUST** abort with the specific error defined in FR-001. No substitution from other verified datasets (e.g., SCS-only datasets) is permitted as they lack the critical post-feedback outcome variables. |
| **SCS (parquet)** | `https://huggingface.co/datasets/tobaba2001/scs_phase2_ts_dataset/...` | Contains SCS scores only. | **NOT SUITABLE**. Lacks feedback condition and post-feedback outcomes. |
| **OSF (parquet)** | `https://huggingface.co/datasets/cjziems/osf_loglikelihood/...` | Log-likelihood data, not psychological outcomes. | **NOT SUITABLE**. |

**Decision**: The pipeline relies exclusively on the OSF source specified in the spec. If the dataset is unavailable, the project halts. No alternative dataset is used to prevent "dataset mismatch" errors. The project is **Data-Contingent**; success requires the existence of the OSF source.

### Statistical Rigor & Assumptions

1.  **Multiple Comparisons**: Holm-Bonferroni correction applied across the 3 primary outcomes and 1 robustness check (SCS-Self-Kindness) as per FR-011.
2.  **Power Analysis**: Spec assumes N=158 available, N=92 required for power (f²=0.02, α=0.05, 1-β=0.80). Pipeline checks N >= 92 (FR-001).
3.  **Causal Inference**: 
    - If dataset metadata confirms randomization: Findings framed as causal.
    - If metadata is absent/ambiguous: Findings explicitly framed as **associational** (FR-017).
4.  **Measurement Validity**: 
    - SCS (Neff, 2003) - Validated.
    - STAI (Spielberger) - Validated.
    - RRS (Nolen-Hoeksema) - Validated.
    - GSES (Schwarzer) - Validated.
5.  **Collinearity**: VIF computed for all predictors. If VIF > 5, collinearity warning issued and independent effects not claimed (FR-013).
6.  **Heteroskedasticity**: Breusch-Pagan test performed. If p < 0.10, HC3 robust SEs used (FR-009).
7.  **Bootstrap**: 5,000 resamples (seed=42) for interaction CI (FR-008). Convergence assessed by CV of SE < 0.05.

### Computational Feasibility
- **Hardware**: CPU-only (2 cores, ~7GB RAM).
- **Methods**: OLS (statsmodels) is computationally trivial for N~150. Bootstrap (5k) is feasible on CPU within 10 mins.
- **Libraries**: `pandas`, `statsmodels`, `scipy` (all CPU-optimized). No GPU/CUDA required.
- **Timeout**: Modeling phase limited to a bounded duration to prevent runner hangs.

## Risk Assessment

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unavailable** | High | Pipeline halts with specific error (FR-001). No fallback to unsuitable datasets. |
| **Insufficient Power** | High | Pipeline checks N >= 92; aborts if lower (FR-001). |
| **Non-Normal Residuals** | Medium | HC3 robust SEs and Bootstrap CIs used. |
| **Collinearity** | Medium | VIF check and warning; no claim of independent effects if VIF > 5. |
| **Randomization Ambiguity** | Medium | Default to "associational" framing (FR-017). |
| **Bootstrap Convergence** | Medium | Retry with a sufficient number of resamples; fallback to parametric CIs with warning. |
| **Historical Data Limitations** | Medium | Report explicitly flags inability to verify participant well-being protocols (Constitution Principle VII). |

## Data Contingency Note

This research question is fundamentally tied to the existence of the OSF dataset `3k9r2`. No verified alternative dataset exists that contains the specific combination of **feedback manipulation** and **pre/post outcome measures**. Consequently:
1.  The pipeline is designed to **abort** if the OSF source is unreachable.
2.  The project does **not** proceed with a "correlational only" analysis, as this would invalidate the specific hypothesis of "moderation of feedback impact."
3.  The "Success" of the project includes the successful retrieval of the data. If data is missing, the pipeline returns a specific "Data Unavailable" status, which is a valid scientific outcome.
