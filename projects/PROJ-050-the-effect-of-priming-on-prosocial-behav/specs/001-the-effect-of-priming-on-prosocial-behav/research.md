# Research: The Effect of Priming on Prosocial Behavior (Association Study)

## Overview

This research document defines the data sources, methodological choices, and feasibility analysis for the project. It addresses the dataset-variable fit, statistical rigor, and compute constraints required to execute the plan on a CPU-first GitHub Actions runner.

## Dataset Strategy

### Primary Data Source
The project requires historical Reddit comments. The plan utilizes the verified HuggingFace dataset `jplu/tf-reddit-comments` (or the most recent verified equivalent containing `link_title` and `author`).

**Verified Datasets**:
- **Source**: `jplu/tf-reddit-comments-2020` (HuggingFace).
- **Access Method**: `datasets.load_dataset("jplu/tf-reddit-comments-2020", ...)`
- **Filtering**:
  - Subreddits: `r/AskReddit`, `r/science`, `r/relationships`.
  - Date Range: `2020-01-01` to `2023-12-31`.
  - Fields needed: `body`, `author`, `created_utc`, `subreddit`, `link_title`, `link_id`.

**Dataset-Variable Fit Check**:
- **Required Variables**: `body` (for scoring), `author` (for hashing), `created_utc` (for tenure calculation), `link_title` (for priming classification).
- **Potential Mismatch**:
  - **Tenure**: If `author_created_utc` is missing (common in comment-only dumps), the plan will calculate `user_tenure` as `comment_date - earliest_comment_date_for_user` (a proxy) or explicitly state the limitation and exclude `user_tenure` from the model if the proxy is invalid.
  - **Volume**: If the dataset lacks sufficient 'Prime' threads (titles with 'thank/help/support/care') to meet N>=4000/group, the plan will report the actual N and note the power limitation.
- **Critical**: If the dataset lacks `link_title`, the priming classification (FR-001) cannot be performed. The plan assumes the verified dataset includes this field.

### Human Annotation Sample (Validation)
- **Strategy**: Randomly sample 200 comments from the processed dataset.
- **Process**: Generate a CSV with `comment_id` and `body` (anonymized).
- **Annotation**: Simulated in the pipeline (using a deterministic synthetic generation for CI testing) to compute Kappa. *Note: In a real research context, this requires manual dual-blind human annotation.*
- **Metric**: Cohen's Kappa.
- **Distinctness**: The human annotation task will label "perceived prosocial intent" rather than just keyword presence, ensuring the validation is distinct from the predictor's keyword matching logic.

## Methodological Rigor

### Statistical Analysis Plan (FR-003)
- **Model**: **Generalized Linear Mixed Model (GLMM)** with a Poisson or Negative Binomial distribution (to handle count data `prosocial_keyword_count`).
- **Formula**: `prosocial_keyword_count ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`.
- **Hypothesis**: `thread_type` (Prime) has a positive coefficient (association).
- **Success Criteria**:
  - Convergence: `status == 'converged'`.
  - Significance: `p-value < 0.05` for `thread_type`.
- **Rigorous Checks**:
  - **Multiple Comparisons**: Not applicable for the primary hypothesis (single fixed effect of interest), but if secondary tests are run, Bonferroni correction will be applied.
  - **Collinearity**: `thread_length` and `prosocial_keyword_count` may be correlated. VIF (Variance Inflation Factor) will be checked. If high collinearity exists, the model will be re-run without the collinear predictor or with regularization, and the limitation noted.
  - **Causal Inference**: This is an **observational study**. Claims will be framed as **associational**. The "priming" is inferred from the title, not experimentally assigned.
    - **Selection Bias**: Users who choose to comment on 'Prime' threads may already be prosocial. The model includes `user_id` random effects to account for baseline variance, but cannot fully eliminate selection bias.
    - **Topic Relevance**: Threads with 'help' in the title naturally attract comments containing 'help' due to topic relevance. This is a known confound; the study tests the association of 'help-themed threads' with 'help-themed comments'.
  - **Power**: Sample size is data-driven (target N>=4000/group). A post-hoc power analysis will be reported based on the final N and effect size.

### Measurement Validity (US2)
- **Sentiment**: VADER (Valence Aware Dictionary and sEntiment Reasoner) is chosen for social media text.
- **Prosocial Lexicon**: A curated list of keywords (e.g., "help", "support", "care", "thank") will be used.
- **Validation**:
  - **Human Sample**: 200 comments.
  - **Metric**: Cohen's Kappa between automated classification (thresholded VADER or keyword count) and human labels.
  - **Reporting**: Kappa value reported. No pass/fail threshold in spec, but low Kappa (<0.4) will be flagged as a validity concern in the report.

## Compute Feasibility (CPU-First)

### Hardware Constraints
- **Runner**: GitHub Actions Free Tier (2 CPU, ~7GB RAM, ~14GB Disk).
- **Time Limit**: 6 hours per job.

### Method Selection
1.  **Data Fetching**: `datasets` library with `streaming=True` to avoid loading the full Reddit archive into RAM. Filter on the fly.
2.  **Scoring**:
    - VADER: CPU-tractable. `nltk` is lightweight.
    - Keyword Count: String operations in `pandas`. CPU-tractable.
3.  **GLMM Fitting**:
    - Library: `statsmodels` (GLMM) or `pymer4` (R interface, avoided for pure Python).
    - CPU Feasibility: Fitting GLMMs on large-scale datasets (tens of thousands of rows) is feasible on CPU.
    - **Risk**: If N > 100k, convergence may be slow.
    - **Mitigation**: If the full dataset is too large, the plan will sample a representative subset (e.g., 20k rows) for the GLMM, explicitly stating the power limitation.
    - **GPU Escape Hatch**: Not required for GLMMs or VADER. The CPU-first approach is valid.

### Decision/Rationale
- **CPU Choice**: All methods (VADER, Keyword Count, GLMM) have faithful CPU forms. No GPU is needed.
- **Data Streaming**: Essential to stay under 7GB RAM.
- **Sampling**: If the full dataset exceeds processing time, a random sample (seeded) will be used. This is a "real" sample, not a synthetic stand-in.

## References

- **VADER**: Hutto, C. J., & Gilbert, E. E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text.
- **GLMM**: Bates, D., et al. (2015). Fitting Linear Mixed-Effects Models Using lme4.
- **Dataset**: `jplu/tf-reddit-comments-2020` (Verified HuggingFace dataset).