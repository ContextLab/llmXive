# Research: Evaluating the Impact of Code Generation on Code Review Turnaround Time

## Overview

This research study investigates the association between **explicitly flagged AI-assisted code contributions** (identified via commit messages and labels) and code review turnaround times. The study leverages the GitHub REST API to fetch data from a representative set of top Python and JavaScript repositories by star count. Due to the heuristic nature of the classification, the study measures the impact of *flagging* AI usage, acknowledging that this may not capture all AI-assisted contributions.

## Dataset Strategy

### Data Source
- **Source**: GitHub REST API (v3)
- **Target Repositories**: Top Python and JavaScript repositories by star count.
- **Data Fields**: `created_at`, `merged_at`, `labels`, `commit_messages`, `repository_name`, `pr_id`, `additions`, `deletions`, `author_login`.
- **Verification**: No external dataset URLs are used; all data is fetched dynamically from the GitHub API.

### Data Acquisition Plan
1. **Fetch Top Repos**: Use GitHub API to retrieve top 10 Python and JS repos by stars.
2. **Fetch PRs**: For each repo, fetch all PRs (handling pagination).
3. **Fetch Commits**: For each PR, fetch commit messages to inspect for AI keywords.
4. **Covariate Collection**: Extract `additions` + `deletions` (PR size) and `author_login` (to calculate author activity/contributions).
5. **Filtering**:
   - Exclude private/archived repos.
   - Exclude PRs with missing `merged_at`.
   - Classify as AI-assisted if:
     - Commit message contains "copilot" OR "ai-generated" (case-insensitive).
     - OR PR labels include "ai-generated", "copilot-assisted", or "llm-code".
   - Otherwise, classify as non-AI-labeled.
6. **Turnaround Calculation**: `merged_at` - `created_at` (in calendar hours, including weekends/holidays).

### Dataset Limitations & Mitigations
- **False Negatives (Misclassification)**: AI contributions may not be labeled. Mitigation: Manual spot-check (n=50) of non-AI-labeled PRs to estimate false-negative rate (FR-011). If >10%, include limitation statement (FR-012).
- **Sample Size**: If a repo has <50 PRs after filtering, skip it.
- **API Rate Limits**: Implement exponential backoff with a configurable maximum number of retries.

## Statistical Analysis Plan

### Hypothesis
- **Null Hypothesis (H0)**: There is no difference in the distribution of turnaround times between explicitly flagged AI-assisted PRs and non-AI-labeled PRs, *after controlling for confounding variables*.
- **Alternative Hypothesis (H1)**: There is a difference in the distribution of turnaround times between the two groups.

### Confounding Control Strategy
Turnaround time is known to be driven by PR size and author experience. To avoid spurious correlations:
1. **Covariates**: We collect `PR Size` (additions + deletions) and `Author Activity` (total PRs by author in the last 6 months).
2. **Stratification**: We perform a **Stratified Mann-Whitney U Test** (analogous to Cochran-Mantel-Haenszel logic) where the comparison is performed within strata of PR size (Small, Medium, Large) and Author Activity (Low, High). This controls for these confounders without requiring parametric assumptions.
3. **Sensitivity**: If stratification is not feasible due to small sample sizes in strata, we will report the univariate result with a strong caveat about confounding.

### Methodology
1. **Descriptive Statistics**:
   - Calculate mean, median, standard deviation, and quartiles (Q1, Q3) for both groups.
   - Report median star count and median number of contributors for selected repos (FR-013).
2. **Outlier Handling**:
   - **Primary Analysis**: Use the **full dataset** for the Mann-Whitney U test. The test is non-parametric and robust to outliers; removing them pre-test can bias results (p-hacking risk).
   - **Visualization**: Use IQR bounds (Q1 - 1.5×IQR, Q3 + 1.5×IQR) *only* for boxplot whiskers to visualize distribution shape.
   - **Sensitivity Check**: Run a secondary analysis with IQR removal to assess robustness, but report the full-dataset result as primary.
3. **Hypothesis Testing**:
   - **Test**: Stratified Mann-Whitney U test (or univariate if strata are too sparse).
   - **Metrics**: U statistic, p-value, effect size (r = Z / sqrt(N)).
   - **Significance Level**: α = 0.05 (SC-004).
4. **Multiple Comparisons**:
   - Only one primary comparison (AI vs. Non-AI). No family-wise error correction needed unless additional sub-tests are introduced.

### Power & Sample Size
- **Justification**: The study relies on a large, naturally occurring dataset.
- **Minimum Detectable Effect Size (MDES)**: We target a small-to-medium effect size.
- **Stopping Rule**: If the AI-labeled group size is **< 30** after data cleaning, the primary hypothesis test is **aborted**. The study will report only descriptive statistics and the limitation that the sample is insufficient for reliable inference. This prevents false negatives due to low power.

### Causal Inference & Validity
- **Observational Study**: This is an observational study. Claims are limited to associational differences.
- **Construct Validity**: The study measures the impact of *explicitly flagging* AI usage, not necessarily *all* AI usage. High false-negative rates will bias the result toward the null (underestimating the effect).
- **Selection Bias**: The "AI" group consists of authors who explicitly flag AI use, which may correlate with specific behaviors (e.g., more cautious, different communication style). The stratified analysis controls for PR size and author activity to mitigate this, but residual confounding may exist.
- **Sensitivity Analysis**: We will use the false-negative rate from the spot-check (FR-011) to simulate a bias-corrected estimate, acknowledging the uncertainty.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Stratified MWU over Univariate MWU** | Controls for known confounders (PR size, author activity) without assuming normality. |
| **Full Dataset for Testing** | Mann-Whitney U is robust to outliers; pre-test removal risks biasing the p-value. |
| **IQR for Visualization Only** | Preserves the integrity of the statistical test while allowing standard boxplot visualization. |
| **Stopping Rule (n < 30)** | Prevents reporting unreliable results from underpowered samples. |
| **Manual Spot-Check** | Essential for quantifying the misclassification bias inherent in the heuristic. |
| **CPU-only implementation** | Ensures feasibility on GitHub Actions free-tier; statistical methods are lightweight. |

## Edge Cases & Handling

| Edge Case | Handling Strategy |
|-----------|-------------------|
| **Repo with <50 PRs** | Skip repo, log warning, exclude from analysis. |
| **No AI-labeled PRs in repo** | Log scenario, exclude repo from final analysis. |
| **API rate limit** | Exponential backoff (limited by a maximum retry threshold), then fail gracefully. |
| **Missing `merged_at`** | Exclude PR, log count. |
| **Small AI sample (<30)** | Abort primary test; report descriptive stats and limitation. |
| **Strata too small** | Fall back to univariate test with explicit caveat about confounding. |

## Success Criteria Alignment

- **SC-001**: Stratified Mann-Whitney U test compares distributions against null hypothesis.
- **SC-002**: Descriptive statistics (mean, median, SD, quartiles) reported for both groups.
- **SC-003**: Data quality measured by % processed PRs (≥95% target); exclusions logged.
- **SC-004**: Significance assessed at α = 0.05.
- **SC-005**: Boxplot generated at ≥300 DPI with proper labels.

## Limitations

- **Heuristic-based Classification**: AI labels are inferred from keywords/labels, not ground truth. False-negative rate estimated via spot-check.
- **Observational Nature**: Cannot infer causality; confounding factors (e.g., repo size, contributor experience) controlled via stratification but not eliminated.
- **Selection Bias**: The "AI" group represents authors who explicitly flag AI use, which may differ systematically from others.
- **Sample Sensitivity**: If the AI group is small (<30), the study lacks power to detect effects.
- **Time Sensitivity**: Data reflects a specific point in time; trends may change.
