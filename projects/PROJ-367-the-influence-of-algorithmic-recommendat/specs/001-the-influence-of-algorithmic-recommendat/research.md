# Research: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Research Question
How does the content diversity of algorithmic recommendations predict subsequent learner course topic diversity, controlling for baseline interests?

## Theoretical Background
The study investigates the "filter bubble" or "echo chamber" effect in educational recommendation systems. While algorithms often optimize for relevance (exploitation), they may inadvertently reduce exposure to novel topics (exploration). The core hypothesis is that higher diversity in recommendations (predictor) correlates with higher diversity in subsequent enrollments (outcome), even after controlling for a user's historical preferences (baseline).

Key concepts:
- **Exploration vs. Exploitation**: The trade-off between trying new topics and sticking to known interests.
- **Shannon Entropy**: A measure of diversity in the distribution of categories.
- **Propensity Score Weighting (PSW)**: A statistical technique to balance *observed* confounders in observational studies. *Note: This study acknowledges the limitation that PSW cannot account for unmeasured confounders.*
- **Outcome Permutation Test**: A non-parametric test to assess the significance of an association by shuffling the dependent variable (outcome) while holding predictors fixed, generating a valid null distribution under the assumption of no association.
- **E-value**: A sensitivity analysis metric that quantifies the minimum strength of association an unmeasured confounder would need to have with both the treatment and the outcome to explain away the observed effect.

## Dataset Strategy

### Primary Data Source
The study requires a dataset with distinct columns for `recommended_categories` and `enrolled_categories` for the same user sessions.

**Verified Datasets**:
- **PSW (parquet)**: The provided verified sources (e.g., `) are inspected.
 - *Constraint*: The spec explicitly requires `recommended_categories` and `enrolled_categories`. The verified PSW datasets (e.g., `pick_and_place`, `record-test`) appear to be robotics or general action datasets, not necessarily educational course enrollments.
 - *Action*: The implementation will first attempt to load the verified Hugging Face datasets using `datasets.load_dataset`. If the schema does not match (missing required columns), the system will raise `DataSchemaError` (FR-007) as mandated.
 - *Fallback*: **No verified real-world educational dataset matching the required schema was found in the provided list.** Consequently, the research component will be limited to a **methodological demonstration** using a **synthetic dataset**. This synthetic dataset will be generated with a fixed seed to mimic realistic user-algorithm interactions, ensuring temporal separation between recommendations and enrollments.
 - *Critical Note*: The study's core research question regarding *real* algorithmic influence on *real* human behavior cannot be empirically tested in this iteration due to the lack of a verified data source. The results will be interpreted as a demonstration of the *methodology* rather than an empirical finding about the educational domain.

### Data Preprocessing
1. **Ingestion**: Load data, validate columns (FR-007). If no verified data, generate synthetic data with a fixed seed.
2. **Cleaning**: Handle missing `enrolled_categories` (exclude or flag).
3. **Semantic Merging**: Merge categories with similarity < threshold (FR-009).
4. **Baseline Vector**: Compute historical preference vector for each user (FR-002).

## Causal Diagram and Conditioning Set

To address the risk of M-bias and collider bias, the following Directed Acyclic Graph (DAG) is assumed:

- **U** (Unmeasured Confounder, e.g., motivation) -> **Baseline_Interest**
- **U** (Unmeasured Confounder) -> **Enrollment**
- **Baseline_Interest** -> **Recommendation**
- **Recommendation** -> **Enrollment**

The `Baseline_Interest_Vector` is a pre-treatment covariate. Conditioning on it is necessary to block the backdoor path from `Recommendation` to `Enrollment` via `Baseline_Interest`. However, if `U` exists, it creates an unblocked backdoor path. The plan acknowledges this limitation and uses **E-values** to quantify the robustness of the association against unmeasured confounding.

## Methodology

### 1. Diversity Metric Calculation (FR-001, FR-009)
- **Metric**: Shannon Entropy ($H = -\sum p_i \log_2 p_i$).
- **Inputs**: `recommended_categories`, `enrolled_categories`.
- **Process**:
 - Count category frequencies.
 - Calculate probabilities.
 - Compute entropy.
 - Handle single-category lists (entropy = 0).
 - Handle empty lists (score = null, exclude).
- **Semantic Threshold Justification**: The entropy metric is sensitive to the semantic similarity threshold. The sweep range {0.01, 0.05, 0.1} is based on standard practices in NLP and recommendation systems literature. The sensitivity analysis is designed to bound the uncertainty of the metric rather than assume a single "correct" threshold.

### 2. Propensity Score Weighting (FR-002, FR-003)
- **Goal**: Balance `Baseline_Interest_Vector` across levels of `Recommendation_Diversity` to control for *observed* confounding.
- **Model**: Logistic regression to estimate propensity scores $e(x) = P(T=1|X)$.
- **Weights**: Stabilized weights $w = \frac{P(T)}{e(x)}$.
- **Diagnostics**: Check for extreme weights (>10x median) and effective sample size reduction. If weights are unstable or the model fails to converge, **fall back to standard linear regression with robust standard errors**.
- **Unmeasured Confounding**: Calculate the **E-value** to quantify the robustness of the association against unmeasured confounders.

### 3. Robustness Verification (FR-004, FR-005)
- **Outcome Permutation Test** (Replaced Residual Permutation):
 - Fit the weighted model (or fallback GLS).
 - Extract the observed coefficient for `Recommendation_Diversity`.
 - Shuffle the `Learner_Diversity` outcome variable [deferred] times (FR-004) while keeping predictors fixed.
 - Re-fit the model for each permutation to build a null distribution of coefficients.
 - Compare the observed coefficient to the 95% CI of the null distribution.
 - *Rationale*: This test is valid under the null hypothesis of no association, whereas shuffling residuals is invalid when unmeasured confounders exist.
- **Sensitivity Analysis**:
 - Sweep semantic similarity thresholds: {0.01, 0.05, 0.1}.
 - Re-run the full pipeline for each threshold.
 - Report coefficient and p-value stability (FR-005).

### 4. Handling Small Samples (FR-008)
- If unique users < 30:
 - Switch to Generalized Least Squares (GLS) with robust standard errors.
 - Log the methodological change.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: The sensitivity analysis involves 3 tests. A Bonferroni correction or similar will be considered if the sweep is treated as a family of tests, though the primary focus is on stability.
- **Power**: The study acknowledges power limitations if the dataset is small. The permutation test is non-parametric and robust to small samples.
- **Causal Framing**: All results are framed as **associational** (FR-006). No claims of causality are made.
- **Collinearity**: `Baseline_Interest_Vector` and `Recommendation_Diversity` are likely correlated. The plan explicitly checks VIF and flags if > 5.0 (SC-004).
- **Dataset Fit**: The plan explicitly checks if the chosen dataset contains the required variables. If not, it uses a synthetic dataset for pipeline demonstration, clearly labeling the limitation.

## Compute Feasibility

- **CPU-First**: All methods (entropy, logistic regression, linear regression, permutation test) are computationally tractable on 2 CPU cores and 7 GB RAM.
- **Data Streaming**: If the dataset is large, `datasets.load_dataset(streaming=True)` will be used.
- **No GPU Required**: No deep learning models or large language models are needed for this analysis.

## Decision/Rationale

- **Why PSW?**: To address the confounding of baseline interests, which is the primary threat to validity in this observational design. *Limitation: Cannot account for unmeasured confounders.*
- **Why Outcome Permutation?**: To provide a distribution-free assessment of significance that is valid under the null hypothesis of no association, avoiding the exchangeability violation of residual shuffling.
- **Why CPU?**: The statistical methods are lightweight; no GPU acceleration is necessary or beneficial for this specific analysis.
- **Dataset Choice**: The plan prioritizes verified Hugging Face datasets. If none match the schema, a synthetic dataset is generated to demonstrate the *methodology* as per the spec's acceptance scenarios, ensuring the pipeline is functional even if the specific educational data is unavailable in the verified list.
