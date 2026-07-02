# Research: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Research Question
Does the adoption of LLM-based code completion tools correlate with changes in developer cognitive load proxies (review comment length, iteration count, review thread depth, and revert frequency) in open-source software projects?

## Dataset Strategy

### Primary Data Source
The study relies on public GitHub repository metadata. The "Verified datasets" block indicates a specific CPU-only dataset for a different task (MixSub-LLaMA), which is **not** suitable for this study as it lacks repository-level PR metadata, LLM configuration files, or developer interaction logs.

Therefore, the data source is **GitHub Public API** (v3), accessed directly via the `code/ingest.py` script.
- **Source**: GitHub REST API (` Name or service not known)"))])
- **Access Method**: Programmatic requests with exponential backoff (as per Edge Cases in spec).
- **Scope**: A curated list of ~50 repositories known or suspected to use LLM tools (identified via `.cursorrules`, `copilot` configs, or commit message patterns) and a matched control group.

### Variable Verification & Fit
The plan confirms the dataset-variable fit for the required metrics:
1. **LLM Adoption Flag**: Derivable from:
 - File existence: `.cursorrules`, `copilot` config files (checked via `GET /repos/{owner}/{repo}/contents`).
 - Commit messages: Scanning last 12 months of commits for "Copilot" or "LLM" keywords (checked via `GET /repos/{owner}/{repo}/commits`).
 - Documentation: Scanning `README.md` and `CONTRIBUTING.md` for mentions (checked via `GET /repos/{owner}/{repo}/contents`).
2. **Cognitive Load Proxies**: Derivable from PR metadata:
 - *Comment Length*: Sum of characters in PR review comments (`GET /repos/{owner}/{repo}/pulls/{pull_number}/comments`).
 - *Iteration Count*: **Total count of push events** to the PR branch between open and merge. **Note**: We explicitly **DO NOT** exclude commits with "Copilot" or small diffs to avoid circular logic bias (see Plan Spec Conflict Resolution).
 - *Review Thread Depth*: Max nesting of comments in review threads (`GET /repos/{owner}/{repo}/pulls/{pull_number}/comments`).
 - *Revert Frequency*: Count of PRs marked as "merged" but subsequently reverted (checked via commit message patterns or PR status).
3. **Control Variables**:
 - *Project Size*: Total lines of code (derived from `GET /repos/{owner}/{repo}/contents` tree or `GET /repos/{owner}/{repo}/stats/code_frequency`).
 - *Team Size*: Count of unique contributors (`GET /repos/{owner}/{repo}/contributors`).
 - *Domain Complexity*: Count of unique languages + top-level dependencies (parsed from `package.json`, `requirements.txt`, etc., retrieved via `GET /repos/{owner}/{repo}/contents`).

**Dataset Limitation Note**: The study relies on *observational* data. There is no random assignment of LLM tools. Therefore, the analysis will strictly frame results as **associational**, not causal.

## Methodology

### Phase 1: Data Ingestion & Classification (FR-001, FR-002 Override)
1. **Repository Selection**: Select ~50 repositories, ensuring each has ≥10 PRs in the last 12 months (SC-001).
2. **LLM Flagging**:
 - Scan for config files (`.cursorrules`, `copilot`).
 - Scan commit messages (≥5% threshold for "Copilot"/"LLM").
 - Scan documentation.
 - *Decision*: If any condition is met, `llm_adoption_flag = 1`. Else `0`.
3. **Metric Extraction**:
 - For each PR in the last 12 months:
 - Extract comment text (calculate length).
 - **Extract iteration count**: Count **ALL** push events to the PR branch. **Do not exclude** commits with "Copilot" or small diffs (critical to avoid circular bias).
 - Extract review threads (calculate depth).
 - Check for revert events.
 - *Filtering*: Exclude repositories with <10 PRs in the last 12 months (SC-001).

### Phase 2: Statistical Analysis (FR-003, FR-004, FR-005)
1. **Model Specification**:
 - **Hierarchical Structure**: Use **Mixed-Effects Models (GLMM)** with random intercepts for `repo_id` to account for PRs nested within repos (addressing ecological fallacy).
 - **Outcome Distribution**: Perform Shapiro-Wilk tests on residuals.
 - If data is **zero-inflated** (common for `revert_frequency` and `iteration_count`): Fit a **Zero-Inflated Negative Binomial (ZINB)** model or a **Hurdle model**.
 - If not zero-inflated but non-normal: Fit a standard **Negative Binomial GLMM**.
 - If normal: Use Linear Mixed Model (LMM).
 - **Predictors**: $Y = \beta_0 + \beta_1 \cdot \text{LLM\_Flag} + \beta_2 \cdot \text{LOC} + \beta_3 \cdot \text{Contributors} + \beta_4 \cdot \text{Complexity} + \text{Random}(repo) + \epsilon$
 - $Y$ iterates over: `avg_comment_length`, `iteration_count`, `review_thread_depth`, `revert_frequency`.
2. **Collinearity Check & Handling**:
 - Calculate Variance Inflation Factor (VIF) for predictors.
 - **Threshold**: If VIF > 5.0, specifically between `lines_of_code` and `domain_complexity` (which are likely correlated as different transformations of project scale), **replace both variables with a single PCA-derived 'Project Scale' factor**. This preserves the signal while eliminating multicollinearity, rather than simply dropping one variable which might lose the domain complexity signal.
3. **Multiple Comparison Correction (FR-004)**:
 - Apply Bonferroni correction to the p-values of the four hypothesis tests ($\alpha_{adj} = \alpha / 4$).
4. **Sensitivity Analysis (FR-005)**:
 - Sweep `iteration_count` definition threshold over {1, 2, 3} updates (using the **non-excluded** count).
 - Report the variation in the coefficient $\beta_1$ for the primary outcome.
5. **Misclassification Sensitivity Analysis**:
 - Vary the `llm_adoption_flag` definition (e.g., require BOTH config file AND commit keywords vs. EITHER) to bound the potential bias from measurement error.

### Phase 3: Reporting (FR-006)
1. Generate a forest plot of effect sizes ($\beta_1$) with 95% CIs for all four proxies.
2. Generate a sensitivity analysis table/plot.
3. Draft the report text, explicitly stating the **associational** nature of findings (SC-005).

## Decision Rationale & Rigor

### Power Analysis Justification
With a sample size of N=50 repositories and 3 control variables, the study has approximately **[deferred] power to detect a large effect size (Cohen's f^2 >= 0.35)** at $\alpha = 0.05$. The study is **underpowered** for small-to-moderate effects (f^2 < 0.15). Therefore, the study is framed as an **exploratory signal detection** phase. Results are interpreted as effect estimates with wide confidence intervals for small effects, rather than definitive rejections of the null hypothesis for small effects. This justification aligns with the constraints of the GitHub API and computational budget while maintaining scientific rigor.

### Why this dataset?
The GitHub Public API is the only viable source for the required variables (PR comments, commit history, config files) at the scale of this study. No pre-packaged dataset (like the verified MixSub dataset) contains the specific "LLM adoption flag" derived from config files or the granular PR review metrics required.

### Statistical Rigor (Addressing Panel Concerns)
- **Hierarchical Data**: Mixed-Effects Models (GLMM) with random intercepts for repos are used to account for the nested structure (PRs within repos), avoiding ecological fallacy.
- **Zero-Inflation**: Explicit use of Zero-Inflated Negative Binomial (ZINB) or Hurdle models for outcomes with excess zeros (reverts, iterations), preventing biased estimates from standard GLMMs.
- **Multiple Comparisons**: Bonferroni correction is explicitly planned for the four dependent variables to control Family-Wise Error Rate (FWER).
- **Collinearity**: VIF diagnostics will be run with a threshold of 5.0. If exceeded, specifically between LOC and domain complexity, a PCA-derived 'Project Scale' factor will replace both variables to preserve signal without multicollinearity.
- **Measurement Error**: A sensitivity analysis varying the adoption threshold (config vs. keywords) is included to bound the bias from non-differential misclassification.
- **Causal Framing**: The plan strictly avoids causal language. The observational nature is highlighted.
- **Measurement Validity**: The proxies (comment length, iteration count) are standard behavioral correlates of cognitive load in software engineering literature. The plan acknowledges this is an operationalization, not a direct psychometric measure (like NASA-TLX), due to data constraints.

### Compute Feasibility
- **Hardware**: CPU-only (GitHub Actions free tier).
- **Libraries**: `scikit-learn`, `statsmodels`, and `scipy` are lightweight and CPU-optimized.
- **Data Volume**: ~50 repos × ~20 PRs/repo = ~1000 PRs. Data size < 100MB.
- **Runtime**: Ingestion (API calls) may take several hours due to rate limits (handled by backoff). Analysis and reporting < 30 minutes. Total well within 6-hour limit.