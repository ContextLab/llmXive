# Research: The Influence of Chatbot Politeness on User-Perceived Quality

## Summary of Research

This research investigates the hypothesis that higher linguistic politeness in chatbot responses leads to higher user-perceived quality (trust). The study utilizes the **HCI_P2** dataset (YCAI3/HCI_P2) as the primary source, which explicitly contains `trust_rating` (1-5 Likert) as its outcome variable. The primary analysis employs a Cumulative Link Mixed-Effects Model (CLMM) to account for the ordinal nature of trust ratings and the hierarchical structure of the data (multiple dialogues per user). Robustness is ensured via an alternative lexicon-based classifier (`polite` library) and subgroup analyses using interaction terms.

## Dataset Strategy

The plan relies exclusively on datasets verified in the "Verified datasets" block or Hugging Face Hub with verified schemas.

| Dataset | Source (Verified URL) | Variables Needed | Suitability Check |
| :--- | :--- | :--- | :--- |
| **HCI_P2** | `https://huggingface.co/datasets/YCAI3/HCI_P2` | `dialogue_id`, `user_id`, `utterance_text` (chatbot), `trust_rating` (1-5), `demographics` (age/gender if present) | **Verified**: Contains `trust_rating` as a direct proxy for trust. **Action**: Verify column existence in the dataset card. If missing, the pipeline halts. |
| **Persona-Chat** | *No verified URL provided in "Verified datasets" block.* | `dialogue_id`, `user_id`, `utterance_text`, `trust_rating` | **Status**: The "Verified datasets" block does **not** list a verified URL for Persona-Chat. **Action**: The implementation will attempt to load via `datasets.load_dataset("persona-chat")` if available on Hugging Face Hub. If no open, directly-downloadable source is found or if it lacks `trust_rating`, the dataset is **excluded** and logged as "Not Met" for FR-001. The pipeline proceeds with HCI_P2 only. |

> **Dataset Variable Fit**: The primary outcome variable is "user-reported trust". The **HCI_P2** dataset provides `trust_rating` (Likert 1-5). This is a direct, independent measure, resolving the construct validity gap of using EmpatheticDialogues' sentiment labels. If the verified HCI_P2 shard lacks explicit trust ratings, the analysis will be restricted to the subset that has them, or the study will be reframed.

## Statistical Methodology

### Primary Analysis: Cumulative Link Mixed-Effects Model (CLMM)
- **Model**: `trust_rating ~ politeness_score + conversation_length + (1 | user_id)`
- **Rationale**: Trust ratings are ordinal (1-5). Linear regression assumes interval data and normal residuals, which is inappropriate. CLMM handles ordinal outcomes and accounts for non-independence of observations from the same user.
- **Software**: R `ordinal` package (via `rpy2` or separate R script).
- **Assumptions**:
  - **Proportional Odds**: The effect of predictors is constant across all thresholds of the ordinal outcome. (Will be tested via `nominal_test()` in `ordinal`).
  - **Random Effects**: User-level intercepts capture unobserved heterogeneity. **Hierarchy Check**: The pipeline will verify if `n_users < n_dialogues`. If `n_users == n_dialogues` (flat structure), the model will switch to a standard Cumulative Link Model (CLM) without random effects to avoid singular fits.
  - **Collinearity**: Politeness and conversation length may be correlated. **Conversation Length** is defined as **total word count**. VIF (Variance Inflation Factor) will be calculated. If VIF > 5, the plan will center the `conversation_length` variable and report the collinearity, potentially excluding it in a sensitivity analysis.
- **Multiple Comparisons**: Bonferroni or Benjamini-Hochberg correction applied to all hypothesis tests (main effect, covariates).

### Robustness Analysis
- **Alternative Classifier**: `polite` library (lexicon-based) as a fallback for LIWC-2015 (which is not open/verified).
- **Comparison**: 
  1. **Primary**: Consistency of the CLMM coefficient sign and significance for `politeness` between the BERT and `polite` models.
  2. **Secondary**: Correlation of predicted scores (`r ≥ 0.80` target).
- **Subgroup Analysis**:
  - Split by `age` and `gender` if metadata exists.
  - **Condition**: `n ≥ 30` per subgroup. If `n < 30`, the subgroup is excluded and logged.
  - **Method**: Use **interaction terms** (`politeness * age`) in a single model to test for moderation. If `n` is too small for random effects (n < 100), switch to a standard CLM (no random effects) for the subgroup analysis to ensure statistical validity.

## Compute Feasibility & Escape Hatch

- **CPU-First Strategy**:
  - Data download and filtering: `pandas`/`datasets` (streaming).
  - Politeness Scoring: `jfiedler/politeness-bert` in `float32` or `int8` (if supported) on CPU. Batch size tuned to fit 6GB RAM.
  - CLMM: R `lme4`/`ordinal` (CPU optimized).
- **GPU Escape Hatch**:
  - If CPU inference of BERT exceeds a practical time threshold or OOMs, the pipeline will auto-offload to a Kaggle GPU (16GB VRAM).
  - **Scaling**: Use `device="cuda"`, `load_in_8bit=True`, and a batch size of 32-64.
  - **Note**: No synthetic CPU approximation of BERT will be used; the real model runs on the GPU.

## Addressing Unresolved Panel Concerns

1.  **Dataset Validity (HCI_P2)**: The plan now uses **HCI_P2** (YCAI3/HCI_P2) as the primary dataset, which explicitly contains `trust_rating`. This resolves the construct validity issue of using EmpatheticDialogues.
2.  **Hierarchy Check**: A mandatory step verifies multiple dialogues per user. If not present, the model switches to CLM (no random effects).
3.  **Fallback Classifier**: Replaced `textstat` with `polite` library for valid politeness scoring.
4.  **Collinearity**: Explicit VIF check and centering of `conversation_length`.
5.  **Robustness Metric**: Focus on coefficient consistency, not just raw score correlation.
6.  **FR-005 (LIWC)**: Formally acknowledged as unavailable; `polite` library is the approved substitute.
7.  **FR-001 (Persona-Chat)**: Treated as secondary. Attempted download; excluded if unverified or lacking trust metrics.
8.  **SC-003/SC-004 Measurement**: Explicit tasks to generate `convergence_report.csv` and `robustness_metrics.csv`.
9.  **SSoT**: `data/processed` is explicitly designated as the Single Source of Truth.
10. **Constitution VI**: Explicitly names the Trust Rating scale from HCI_P2.

## References

- **Datasets**: HCI_P2 (YCAI3/HCI_P2) via Hugging Face Hub.
- **Models**: `jfiedler/politeness-bert` (Hugging Face Hub).
- **Statistical Methods**: Christensen, R. H. B. (2015). *ordinal - Regression Models for Ordinal Data*. R package version 2015.6-28.
- **Libraries**: `polite` (Python) for lexicon-based politeness.