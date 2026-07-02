# Research: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Problem Statement & Operationalization

The study investigates whether the **adoption culture** of LLM code completion tools is associated with changes in developer cognitive load, operationalized via public code review metrics.
- **Independent Variable**: `llm_adopted` (Binary: 1 if repo has `.cursorrules`, `copilot` config, or LLM keywords in commit messages; 0 otherwise).
  - *Limitation*: This is a proxy for "tool presence" or "adoption culture," not "usage intensity." Measurement error (misclassification) will likely cause **attenuation bias** (biasing coefficients toward zero), potentially leading to a false negative. Results are interpreted as the association between tool presence and review metrics, representing a lower-bound estimate.
- **Dependent Variables (Proxies)**:
  - `comment_length_chars`: Average length of review comments (proxy for communication effort).
  - `iteration_count`: Number of commits/edits per PR (proxy for review friction).
  - `revert_frequency`: Frequency of reverts within 7 days (proxy for quality/stability).
  - *Validity Check*: The study will only interpret `revert_frequency` as a cognitive load proxy if it shows a significant correlation with `iteration_count` (FR-007). If not, it will be excluded from the primary regression model. `revert_frequency` is theoretically a quality metric, not a direct cognitive load metric; its inclusion as a proxy is conditional on empirical validation.
- **Covariates**: `lines_of_code`, `contributor_count`, `repo_stars`, `repo_fork_count` (as proxies for team maturity/expertise).
  - *Note*: `domain_complexity` is **excluded** from the regression model to avoid mathematical collinearity with `lines_of_code` and `contributor_count`.

## Dataset Strategy

The study requires a curated list of repositories (≥50) with PR metadata.
- **Primary Data Source**: GitHub Public API (programmatic fetching).
  - *Rationale*: No single verified dataset exists that contains both the specific LLM adoption flags (config files/keywords) and the granular PR metrics (iteration count, revert frequency) for a curated list of mixed LLM/non-LLM projects.
  - *Constraint*: The `# Verified datasets` block contains PR samples (e.g., `prs-v2-sample`) but lacks the specific LLM configuration context and the curated control/treatment split required for this specific hypothesis. Therefore, the pipeline must fetch raw data from GitHub to construct the dataset dynamically.
- **Fallback/Sample Data**: For testing the pipeline locally or on CI without hitting rate limits, a small subset of the verified `prs-v2-sample` (HuggingFace) may be used to validate schema compliance, but the primary analysis will rely on the live API fetch from the `target_repos.json` list.

**Dataset Fit Check**:
- The verified PR datasets (e.g., `loubnabnl/prs-v2-sample`) contain PR metadata but **do not** contain the `llm_adopted` flag (derived from repo config) or the specific `revert_frequency` logic (requires cross-referencing merge/revert events).
- *Action*: The implementation will **not** use the verified HuggingFace PR datasets for the primary analysis. It will use the GitHub API to fetch the specific repositories listed in `target_repos.json`. The verified datasets are cited here only to confirm that no suitable pre-processed alternative exists.

## Statistical Methodology

### 1. Propensity Score Matching (PSM)
- **Goal**: Balance covariates (`lines_of_code`, `contributor_count`, `repo_stars`, `repo_fork_count`) between `llm_adopted=1` and `llm_adopted=0` groups.
- **Method**: Logistic regression to estimate propensity scores. Nearest-neighbor matching (1:1) without replacement.
- **Success Criterion**: Standardized Mean Difference (SMD) < 0.1 for all covariates post-matching (FR-006, SC-005).
- **Fallback**: If exact matching fails due to small sample size, use matching with caliper.
- **Limitation**: PSM cannot balance on unobserved confounders.

### 2. Linear Mixed-Effects Model (LMM)
- **Model**: `outcome ~ llm_adopted + lines_of_code + contributor_count + repo_stars + repo_fork_count + (1|repo_id)`
- **Rationale**: Accounts for the nested structure (PRs within Repositories) to prevent pseudoreplication (Scientific Soundness concern). `repo_id` is a random intercept.
- **Collinearity**: `domain_complexity` is **excluded** from the model to avoid perfect collinearity with `lines_of_code` and `contributor_count`.
- **Multicollinearity Check**: Calculate VIF on fixed effects. If VIF ≥ 5, log warning and consider Ridge LMM (if supported) or report instability.
- **Output**: Coefficients, p-values, 95% Confidence Intervals (FR-004, SC-001).

### 3. Construct Validity Gate (FR-007)
- Calculate correlation between `iteration_count` and `lines_of_code`.
- Calculate correlation between `revert_frequency` and `iteration_count`.
- **Decision**: If `revert_frequency` correlation with `iteration_count` is weak (p > 0.05), the study will explicitly state that `revert_frequency` is not a valid proxy for cognitive load in this context and exclude it from the primary regression results.

### 4. Sensitivity Analysis
- **Thresholds**: Vary `min_pr_lines` (e.g., 10, 20, 30).
- **Stratification**: Split by top 3 languages (Python, JS, Java) and repository age (median split).
- **Robustness**: Report effect size variation. Flag "High Sensitivity" if sign flips (FR-005, SC-002).

## Unobserved Confounders & Limitations

-   **Developer Expertise**: High-seniority teams are more likely to adopt new tools (LLMs) AND are likely to have lower cognitive load (faster reviews, fewer reverts) regardless of the tool. This is a critical unobserved confounder. PSM cannot balance it. The study **cannot claim causality**; results are framed as **associational**.
-   **Measurement Error**: The binary `llm_adopted` flag is a noisy proxy for actual usage intensity. This will likely bias the estimated effect toward zero (attenuation bias).
-   **Proxy Validity**: `revert_frequency` is a measure of quality/stability, not cognitive load. Its inclusion as a proxy is conditional on empirical validation (FR-007).

## Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
  - Data fetched in chunks with exponential backoff to avoid API limits.
  - Dataframes kept in memory; if size exceeds 6GB, use **Stratified Sampling** by `llm_adopted` to ensure balance.
  - No GPU-intensive models. `statsmodels` and `linearmodels` are CPU-optimized.
  - Runtime target: < 6 hours (SC-003).
- **Libraries**: `pandas`, `scikit-learn` (for PSM), `statsmodels` (for LMM/VIF), `requests`, `linearmodels`.

## References & Citations

- **Dataset**: GitHub Public API (Programmatic). No static URL.
- **Methodology**:
  - Propensity Score Matching: Rosenbaum & Rubin (1983).
  - Cognitive Load Proxies: Standard SE metrics (iteration count as friction).
  - Mixed-Effects Models: Pinheiro & Bates (2000).
- **Verified Datasets (for schema validation only)**:
  - `loubnabnl/prs-v2-sample`: https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use GitHub API vs. Pre-packaged Dataset** | No verified dataset contains the specific `llm_adopted` flag derived from config files. API fetch is necessary to operationalize the independent variable. |
| **Linear Mixed-Effects Model (LMM)** | Required to handle nested data (PRs within Repos) and prevent pseudoreplication (Scientific Soundness concern). |
| **Exclusion of `domain_complexity`** | Required to avoid mathematical collinearity (Scientific Soundness concern). The spec (FR-003) is flagged for kickback to remove this requirement. |
| **Construct Validity Gate** | Required to ensure `revert_frequency` is a valid proxy for cognitive load (FR-007). If invalid, it is excluded from the primary model. |
| **Stratified Sampling** | Required to ensure both treatment and control groups are represented if sampling is necessary for memory constraints. |
| **Observational Framing** | Despite PSM and LMM, the study cannot claim causality due to unobserved confounders (e.g., Developer Expertise). Results will be framed as "associational" to align with the observational nature of the data (Assumption). |
| **Exclude Repos < 10 PRs** | To prevent statistical noise from dominating the regression (US-1, Edge Cases). |
