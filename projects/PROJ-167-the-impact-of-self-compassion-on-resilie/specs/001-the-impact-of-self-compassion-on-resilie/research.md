# Research: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Executive Summary

This research plan investigates the moderating role of self-compassion (SCS) on the relationship between negative feedback and psychological outcomes (anxiety, rumination, self-efficacy). The analysis relies on an experimental or quasi-experimental dataset hosted on OSF. The methodology prioritizes statistical rigor, including ANCOVA with interaction terms, Holm-Bonferroni corrections, and robust standard errors.

## Dataset Strategy

**Target Dataset**: "Feedback and Self-Compassion" (OSF).
**Specified URL**: `https://osf.io/3k9r2/` (per `spec.md`).

**Verification Status**:
- **CRITICAL**: The URL `https://osf.io/3k9r2/` is **NOT** present in the "Verified datasets" block provided for this planning session.
- **Action**: The implementation pipeline **MUST** treat this as a potential failure point. The code will attempt to fetch the URL. If the fetch fails, the dataset format is invalid, or the required columns are missing, the pipeline will abort with `DATA_UNAVAILABLE`.
- **Alternative**: If the OSF link is broken, the plan cannot proceed with this specific dataset. No substitute dataset is proposed as the variables (specific post-feedback measures) are unique to the study design.

**Required Variables**:
| Variable | Description | Source Column (Expected) |
|----------|-------------|--------------------------|
| `SCS_Total` | Self-Compassion Scale Total Score | `scf_total` |
| `SCS_SelfKindness` | Self-Compassion Subscale | `scf_self_kindness` |
| `Anxiety_Pre` | Baseline Anxiety (STAI) | `stai_pre` |
| `Anxiety_Post` | Post-Feedback Anxiety | `stai_post` |
| `Rumination_Pre` | Baseline Rumination (RRS) | `rrs_pre` |
| `Rumination_Post` | Post-Feedback Rumination | `rrs_post` |
| `SE_Pre` | Baseline Self-Efficacy (GSES) | `gse_pre` |
| `SE_Post` | Post-Feedback Self-Efficacy | `gse_post` |
| `Feedback_Cond` | Experimental Condition | `feedback_cond` |
| `Age` | Participant Age | `age` |
| `Gender` | Participant Gender | `gender` |
| `BigFive` | Personality Traits (Optional) | (If present) |

**Dataset Availability Check**:
- **Status**: **UNVERIFIED**.
- **Plan**: The `download.py` script will attempt to access `https://osf.io/3k9r2/`. If successful, it will validate the CSV structure. If the URL is unreachable or the data is missing required columns, the script exits with code 1 and the message: `[DATA_UNAVAILABLE: Required columns missing from source. The dataset 'Feedback and Self-Compassion' is required. If unavailable, the pipeline cannot proceed.]`.

## Statistical Methodology

### 1. Data Preparation
- **Listwise Deletion**: Remove rows with missing SCS, baseline, or post-feedback scores (FR-002).
- **Encoding**:
  - `feedback_cond`: Categorical. Reference = 'Positive Feedback' (0). Levels: Neutral (1), Negative (2).
  - `SCS`: Z-scored (`SCS_z`).
- **Centering**: Interaction terms constructed from centered variables to ensure orthogonality.
- **Covariates**: Baseline scores (`stai_pre`, `rrs_pre`, `gse_pre`), Age, Gender.
- **Big Five**: Conditionally included if present (FR-018).
- **Interaction**: `C(feedback)[T.2]:SCS_z` (Negative Feedback × Self-Compassion).

### 2. Primary Analysis (ANCOVA)
- **Model**: $Y_{post} = \beta_0 + \beta_1(Y_{pre}) + \beta_2(SCS\_z) + \beta_3(Feedback) + \beta_4(Feedback \times SCS\_z) + \epsilon$
- **Estimation**: OLS via `statsmodels`.
- **Robustness**: HC3 Standard Errors (FR-009).
- **Correction**: Holm-Bonferroni across the 3 primary outcomes (FR-011).

### 3. Homogeneity of Regression Slopes (FR-019)
- **Test**: Fit interaction between `Covariate` and `Feedback`.
- **Violation Handling**: If significant (p < 0.10), the standard ANCOVA is invalid. The plan **does not** use Johnson-Neyman. Instead, it runs a **Stratified Analysis** (separate models per feedback group) or a **Random Slopes Model**. The primary interaction result is flagged as "Uninterpretable under homogeneity violation".

### 4. Robustness & Diagnostics
- **Bootstrap**: 5,000 resamples (seed=42) for interaction CI (FR-008).
- **VIF**: Variance Inflation Factor for predictors (FR-013).
- **Alternative Moderator**: Repeat with `SCS_SelfKindness` (FR-014).
- **Correction**: Separate Holm-Bonferroni for robustness tests (FR-011b).

## Methodological Caveats

1. **Causal Inference**: If the dataset metadata does not explicitly confirm randomization, findings will be framed as **associational** (FR-017).
2. **Power**: If N < 92, a "Power Insufficient" warning is included; only effect sizes and CIs are reported, no p-values.
3. **Dataset Validity**: The primary risk is the unverified status of the OSF URL. The pipeline is designed to fail safely rather than hallucinate results.
4. **Homogeneity Violation**: If the homogeneity of slopes assumption is violated, the primary moderation result is considered uninterpretable, and stratified results are reported instead.
5. **Selection Bias**: If randomization is absent, results may be confounded by pre-existing group differences.