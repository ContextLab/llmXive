# Research: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Executive Summary

This research investigates the associational relationship between the diversity of algorithmic recommendations and subsequent learner course topic diversity. Using public course enrollment datasets, we calculate Shannon entropy (log base 2) for both recommendation lists and enrollment lists directly on the raw category labels. We employ Propensity Score Weighting (PSW) with Overlap Weighting fallback to adjust for the confounding effect of baseline user interests and validate findings through Residual Permutation Tests. All conclusions are framed strictly as associational, avoiding causal claims. **The project requires a verified educational dataset; if none is found, the project is blocked.**

**Key Revision**: The requirement for semantic similarity merging and threshold sensitivity analysis has been removed. Diversity is calculated directly on the raw category labels provided in the dataset to avoid arbitrary definitions.

## Dataset Strategy

The analysis relies on public datasets containing distinct columns for `recommended_categories` and `enrolled_categories` with **educational course topics**. The following datasets have been verified for availability and format:

| Dataset Name | Source URL | Format | Relevance |
| :--- | :--- | :--- | :--- |
| [Educational Dataset Placeholder] | [Verified Educational URL] | Parquet/CSV | **Must contain educational course categories.** |

**Critical Note on Data Availability**: The spec assumes the existence of a dataset with distinct `recommended_categories` and `enrolled_categories` columns. **No analysis will be performed on non-educational data** (e.g., robotics, code, medical data) as it constitutes a category error and invalidates the scientific claim. **If no dataset with explicit "course recommendation" and "course enrollment" columns containing educational topics is found in the verified list, the project is blocked.** The implementation will raise a `DataSchemaError` if the required columns are missing or if the dataset is not educational, as per FR-007.

**Dataset Selection Rationale**:
- **Primary**: If a dataset with the exact schema (user_id, session_id, recommended_categories, enrolled_categories) **and educational course topics** is found in the verified list, it will be used.
- **Fallback**: **There is no fallback to non-educational data.** If no such dataset exists, **the project is blocked** and no further implementation will proceed. **Methodological validation on unrelated data is rejected as it invalidates the scientific claim.**

## Methodological Approach

### 1. Diversity Metric Calculation (FR-001)
- **Metric**: Shannon Entropy ($H = -\sum p_i \log_2 p_i$).
- **Base**: 2 (log base 2), as verified by authoritative sources.
- **Process**:
  1. Use the raw category labels from `recommended_categories` and `enrolled_categories` lists. **No semantic similarity merging is performed.**
  2. Calculate frequency distribution of categories.
  3. Compute entropy. If a list is empty, assign `null` and log a warning.
- **Justification**: Shannon entropy is the standard measure of diversity in information theory, capturing both richness and evenness of the distribution. Direct calculation on raw labels avoids arbitrary thresholding.

### 2. Baseline Control and Propensity Score Weighting (FR-002, FR-003)
- **Baseline Interest Vector**: Derived from pre-study enrollment history. **Users with no prior enrollment history are excluded from the analysis (listwise deletion) to avoid systematic bias from imputation.**
- **Propensity Score**: Estimated using a logistic regression model predicting the likelihood of receiving a "high diversity" recommendation based on the baseline vector and other covariates.
- **Weighting**: Stabilized weights are calculated to balance the distribution of baseline interests across different levels of recommendation diversity.
- **Fallback**: **Fallback to standard linear regression is explicitly rejected.** If weights are extreme (>10x median) or the model fails to converge, **Overlap Weighting is applied** (truncation or formula $w_i = 1 - p_i$) to handle poor overlap. This ensures the analysis remains controlled rather than reverting to a biased unweighted estimate.
- **Collinearity Check**: Variance Inflation Factor (VIF) is calculated. If VIF > 5.0, a limitation is flagged.

### 3. Robustness Verification (FR-004)
- **Residual Permutation Test**: 1,000 iterations of **shuffling the residuals** from the weighted regression model to generate a null distribution. The observed effect size is compared against the confidence interval of this distribution. **This method preserves the weight structure and tests the null hypothesis of no effect after controlling for known confounders.**
- **Outcome Permutation Rejection**: Shuffling the outcome variable is rejected as it ignores the weight structure required for the confounder adjustment and does not test the specific null hypothesis.

### 4. Statistical Rigor and Framing (FR-006)
- **Associational Framing**: All results are explicitly framed as "associational" or "predictive." No causal language (e.g., "causes," "leads to") is used.
- **Multiple Comparisons**: If multiple tests are run, family-wise error correction (e.,g., Bonferroni) is applied where applicable.
- **Power Limitation**: If the sample size (N < 30) is detected, the system switches to a Generalized Least Squares (GLS) model with robust standard errors, and a power limitation is explicitly stated.

## Decision/Rationale

- **CPU-First Approach**: The analysis is designed to run on a CPU-only environment (GitHub Actions free tier). No GPU-accelerated libraries are used. The linear models and permutation tests are computationally tractable for datasets < 100k rows.
- **Dataset Exclusion Strategy**: **No non-educational datasets will be used.** The plan prioritizes scientific validity over methodological validation on unrelated data. **If no verified educational dataset is found, the project is blocked.**
- **Residual vs. Outcome Permutation**: The plan adopts a **Residual Permutation Test** (shuffling residuals) instead of an Outcome Permutation Test. This is critical for testing the null hypothesis of no effect after controlling for known confounders in weighted regression contexts, as it preserves the weight structure.
- **Direct Entropy Calculation**: The plan calculates entropy directly on raw category labels. **Semantic similarity merging is rejected** because it requires a domain-specific ontology that is not available, making the metric arbitrary and invalid.

## Assumptions & Limitations

- **Data Availability**: The plan assumes that a dataset with the exact schema and educational course topics exists. **If no such dataset is found, the project is blocked.**
- **Baseline Proxy**: The "Baseline_Interest_Vector" is assumed to be a sufficient proxy for intrinsic user preferences. **Users with no baseline history are excluded to avoid bias.**
- **Compute Constraints**: The analysis is designed to fit within a reasonable CI limit and standard RAM constraints. If the dataset is larger, streaming is used.
- **Causal Framing**: The study does not claim causality. All findings are framed as associational.
- **Null Results**: **Null results are treated as significant, publishable findings** that challenge assumptions about the power of recommender systems.
- **Runtime**: The pipeline is designed to complete within 6 hours. If it exceeds this, a warning is recorded rather than a hard crash.