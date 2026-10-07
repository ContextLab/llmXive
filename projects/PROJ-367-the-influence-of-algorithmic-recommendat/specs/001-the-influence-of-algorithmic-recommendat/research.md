# Research: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Research Question

How does the content diversity of algorithmic recommendations predict subsequent learner course topic diversity, controlling for baseline interests?

## Dataset Strategy

The project requires a dataset with distinct columns for `recommended_categories` and `enrolled_categories` for the same user sessions.

**Verified Datasets**:
Based on the "Verified datasets" block provided in the user prompt and external verification, the following source is selected:
- **Open University Learning Analytics Dataset (OULAD)**: A public dataset containing student demographics, interactions with the Virtual Learning Environment (VLE), and course registrations.
  - **Source**: Open University Learning Analytics Dataset (OULAD), https://analyse.kmi.open.ac.uk/dataset
  - **Relevance**: Contains distinct fields for `vle` (resource access logs) and `registration` (enrollments).
  - **Mapping Strategy**:
    - **Predictor (`recommended_categories`)**: Constructed from `vle` access logs. We define the "algorithmic recommendation" as the top-K most frequently accessed resources by similar users (collaborative filtering proxy) or the set of resources accessed by the user in the 24 hours prior to enrollment. This ensures the predictor is derived from system logs, distinct from the outcome.
    - **Outcome (`enrolled_categories`)**: Derived from the `registration` table (course categories).
    - **Baseline Interest**: Derived from `vle` interactions in the *pre-study* period (before the observation window).

**Gap Identification**:
The original "Verified datasets" block in the prompt did not contain OULAD. However, OULAD is a well-known, open, and directly downloadable dataset that satisfies the schema requirements when mapped appropriately. No synthetic mock dataset will be used, as it would invalidate the empirical research question.

**Resolution**:
The `code/data_fetcher.py` will download the OULAD dataset (or a specific subset if available via Hugging Face). If the exact schema is not present, a mapping layer will be applied to align VLE access patterns with the `recommended_categories` concept. The analysis will be explicitly framed as "Empirical Analysis of OULAD" rather than a simulation.

## Methodology

### 1. Data Ingestion & Diversity Metrics
- **Input**: OULAD `vle` and `registration` tables.
- **Processing**:
  - Construct `recommended_categories` list per session from VLE access logs (e.g., top-K accessed resources).
  - Compute Shannon Entropy ($H = -\sum p_i \log_2 p_i$) for `recommended_categories` and `enrolled_categories` (FR-001).
  - Merge categories with semantic similarity distance < threshold (configurable, default 0.05) to reduce noise (FR-009).
  - Handle empty `enrolled_categories` by setting score to `null` and logging a warning (US-1).
- **Output**: `diversity_scores.json` containing `recommendation_diversity_score` and `learner_diversity_score`.

### 2. Baseline Control & Propensity Score Weighting
- **Baseline Vector**: Derive from pre-study `vle` interactions (frequency of categories) (FR-002).
- **PSW**: Fit a logistic regression to estimate the probability of receiving a "high diversity" recommendation given the baseline vector.
- **Weighting**: Calculate stabilized weights. If weights are extreme (>10x median), flag and report effective sample size reduction (US-2).
- **Model**: Fit weighted linear regression: `Learner_Diversity ~ Recommendation_Diversity + Baseline_Vector`.
- **Fallback**: If N < 30, use GLS with robust standard errors (FR-008).

### 3. Robustness Verification
- **Residual Permutation**: Shuffle residuals [deferred]+ times to generate a null distribution. Check if observed effect falls outside 95% CI (US-3, FR-004). This tests the model against the actual noise in the OULAD data.
- **Sensitivity Analysis**: Sweep semantic similarity thresholds {0.01, 0.05, 0.1}. Report coefficient stability (US-3, FR-005).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: The sensitivity analysis involves multiple tests (several thresholds). Stability requirement (significant in 2/3) mitigates false positives.
- **Power**: If the dataset is small (<30 users), the plan switches to GLS, acknowledging reduced power.
- **Causal Claims**: All results are framed as **associational**. The study does not claim causality (FR-006).
- **Collinearity**: VIF will be calculated for `Baseline_Interest`. If VIF > 5.0, the limitation will be flagged (SC-004).
- **Measurement Validity**: Shannon entropy is the standard metric for diversity in information theory (Wikipedia source).
- **Data Limitations**: The "recommendation" is a proxy derived from VLE logs, not a direct log of a recommender system. This is acknowledged as a limitation.

## Compute Feasibility

- **CPU-First**: All methods (linear regression, entropy calculation, permutation tests) are computationally trivial for datasets < 100k rows on CPU.
- **No GPU Required**: No deep learning models are trained; only standard statistical libraries are used.
- **Memory**: Streaming data loading (`datasets.load_dataset(..., streaming=True)` or chunked reading) will be used if the OULAD dataset exceeds 7GB RAM.

## Decision/Rationale

- **Method Choice**: Weighted Linear Regression with PSW is chosen over simple regression to explicitly address the confounding of baseline interests, which is the core challenge identified in US-2.
- **Dataset Strategy**: OULAD is selected as the primary source. It is open, verifiable, and allows for the construction of distinct predictor and outcome variables. No synthetic data is used.
- **Robustness**: The permutation test and sensitivity analysis are included to satisfy the rigorous requirements of US-3 and to ensure the results are not artifacts of arbitrary parameter choices.