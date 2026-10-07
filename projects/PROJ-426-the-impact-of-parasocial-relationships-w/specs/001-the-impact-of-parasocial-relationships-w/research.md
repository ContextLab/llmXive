# Research: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Overview

This research plan investigates the longitudinal association between AI companion usage and loneliness, controlling for pre-existing emotional coping styles. The study relies on observational data, necessitating careful handling of confounding variables and strict adherence to associational framing. The study is contingent on the existence and accessibility of the required datasets.

## Dataset Strategy

The analysis requires two primary data sources: a longitudinal self-report dataset and behavioral interaction logs.

| Dataset | Source / Verified URL | Access Method | Relevance to Study |
|:--- |:--- |:--- |:--- |
| **Reddit Loneliness Longitudinal Dataset** | *No verified source found in block.* | **ACTION**: The spec assumes a Zenodo DOI exists. The plan must verify this DOI. If no open source exists, the study must reframe or halt. | Primary outcome (UCLA Loneliness Score), demographics, and baseline text for emotional coping proxy. |
| **Pushshift Reddit Interaction Logs** | *No verified source found in block.* | **API**: ` (or archival mirror). | Behavioral metrics (usage frequency, session duration) for subreddits `r/Replika`, `r/characterAI`, `r/AICompanions`. |
| **ECAR Lexicon** | ` | **Load**: `datasets.load_dataset("12ml/e-CARE")` | Source for emotional coping proxy terms (anxiety/avoidance). |

**Critical Feasibility Note**: The "Verified datasets" block provided for this task does **not** list a verified URL for the *Reddit Loneliness Longitudinal Dataset* or *Pushshift* logs.
- **Action**: The implementation script must first attempt to fetch the Zenodo dataset using the DOI specified in the spec. If the DOI is invalid or the dataset is gated, the pipeline must halt with "Data Linkage Impossible" (per Assumptions).
- **Action**: For Pushshift, the script must use the public API. If the API is unreachable or rate-limited beyond retries, the pipeline halts.
- **Constraint**: No synthetic data or fake mirrors will be generated. The study relies entirely on the existence of these real, open datasets.

**Dataset Variable Fit Check**:
- **Required**: `UCLA_Loneliness_Score`, `username` (for hashing), `timestamp`, `baseline_text` (for lexicon).
- **Verified**: The Zenodo dataset must be inspected at runtime. If `baseline_text` is missing, users are excluded (FR-009). If `username` is missing, matching fails.

**Matching Logic**: The plan assumes the Zenodo dataset contains raw usernames (or a hashable identifier) that can be matched against Pushshift logs. If the Zenodo dataset lacks this, the pipeline halts.

## Methodological Rigor

### Statistical Approach
1. **Model**: Linear Mixed-Effects Model (LMM).
 - **Fixed Effects**: `UsageFrequency`, `SessionDuration`, `EmotionalCopingProxy`, `Age`, `Gender`.
 - **Random Effects**: Random intercept for `User`; Random slope for `UsageFrequency` by `User`.
 - **Structure**: Lagged predictors (Usage at $T$ predicts Loneliness at $T+1$).
2. **Inference**:
 - **Multiple Comparisons**: Family-wise error correction (Bonferroni or Holm) applied to the set of fixed effect tests.
 - **Robustness**: Bootstrap resampling (1,000 iterations, seed=42) to generate 95% CIs.
 - **Power**: Acknowledged limitation if $N < 500$ (per Assumptions). A power analysis will be conducted to determine the detectable effect size.
3. **Causal Framing**: All results framed as **associational**. No causal claims (e.g., "AI usage causes loneliness") will be made.

### Measurement Validity
- **UCLA Loneliness Scale**: Validated instrument; will check completion rates per Constitution Principle VII.
- **Emotional Coping Proxy**: Derived from *ECAR Lexicon* (verified via HuggingFace URL above). **Note**: This proxy measures 'emotional vocabulary' rather than 'attachment disposition'. It is used as a control for emotional expression, not as a direct measure of attachment theory. Validity depends on the lexicon's coverage of emotional terms in AI contexts.

### Data Handling
- **Missing Data**: Users with missing baseline text or emotional coping scores are **excluded** (FR-004b, FR-009). No imputation.
- **PII**: Usernames hashed via SHA-256 immediately upon ingestion. Original usernames never stored.
- **Selection Bias**: A bias analysis will be conducted to compare the demographics of excluded users to included users.

## Computational Feasibility

- **CPU-First**: The plan uses `statsmodels` for LMM and `scikit-learn` for bootstrapping. These are CPU-tractable.
- **Resource Limits**:
 - **RAM**: Streaming the dataset and processing in chunks ensures usage stays <7 GB.
 - **Time**: 1,000 bootstrap iterations on ~500 users is computationally heavy but feasible within 6 hours on 2 cores if optimized (e.g., using `joblib` for parallelization within the CPU limit).
- **GPU Escape Hatch**: Not required. Statistical modeling does not benefit from GPU in this context (small tabular data).

## Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **Dataset Missing** | Pipeline halts with explicit error if Zenodo DOI fails or Pushshift returns empty. |
| **Insufficient Match Rate** | If match rate < 80% (SC-001), report "Power Insufficient" and halt. |
| **Model Convergence Failure** | If LMM fails to converge, reduce random effects complexity (remove random slope) and log warning. |
| **API Rate Limits** | Exponential backoff (5 retries, 30s timeout) implemented in `src/utils/retry_policy.py`. |
| **Power Limitation** | If N < 500, calculate detectable effect size. If d > 0.8, halt with "Power Limitation" warning. |
| **Selection Bias** | Conduct a bias analysis to compare excluded and included users. |