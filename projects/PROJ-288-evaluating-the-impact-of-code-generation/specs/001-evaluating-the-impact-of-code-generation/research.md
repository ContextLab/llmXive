# Research: Evaluating the Impact of Code Generation on Code Review Time

## Executive Summary

This research plan investigates the impact of **explicit LLM disclosure** on code review efficiency. The primary hypothesis is that PRs explicitly disclosing LLM usage ("Disclosing" group) may be reviewed faster (due to perceived cleanliness) or slower (due to scrutiny) compared to PRs that do not disclose ("Non-Disclosing" group).

**Critical Methodological Note**: The study explicitly acknowledges that the "Non-Disclosing" group may contain undisclosed LLM-generated code. Therefore, the comparison measures the **impact of disclosure** rather than the pure impact of **LLM vs. Human code**. The "Disclosing" group is defined by the presence of keywords ("copilot", "llm", "generated") in the PR title or commit message. The "Non-Disclosing" group is a negative control from the same repositories. Any difference observed is attributed to the *signal* of disclosure, not necessarily the *origin* of the code.

The study relies on GitHub PR metadata, a keyword-based labeling strategy, and a SIMEX-corrected regression model, constrained by CPU-only execution and strict data hygiene.

## Dataset Strategy

### Verified Datasets
The following datasets have been verified for reachability and format. **Only these sources** will be used for data acquisition or validation baselines.

| Dataset Name | Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **PRS-v2-sample** | Sample of Pull Request metadata (titles, bodies, timestamps). | ` | **Primary Source**: Initial exploration of PR structure and timestamp availability. |
| **Authors Merged Model PRs** | Merged PR data including author and model information. | ` | **Secondary Source**: Cross-referencing for model-generated tags if available. |
| **Authors Merged Dataset PRs** | Additional merged PR dataset. | ` | **Tertiary Source**: Backup for metadata extraction. |
| **CodeXGLUE / CodeParrot** | Code-specific dataset with human-written and LLM-generated code examples. | `https://huggingface.co/datasets/codeparrot/code-parrot` (or verified equivalent) | **Validation Baseline**: Used to calibrate the "formatting consistency" and "comment density" heuristics on *actual code* (replacing generic text corpora). |
| **Human-Written Baseline Corpus** | A curated subset of human-written code diffs from the above or similar verified code datasets. | (Derived from CodeXGLUE/CodeParrot) | **Baseline for FR-010**: Used to estimate false positive rates of the style heuristics. |

### Dataset Fit Assessment
**CRITICAL NOTE**: The spec requires **Pull Request metadata** (timestamps, code lines, reviewer counts) from **high-star repositories** with **LLM keywords**.
- The verified PR datasets (PRS-v2-sample, etc.) provide metadata but **do not** guarantee the presence of "copilot", "llm", or "generated" keywords in commit messages, nor do they contain the raw code diffs required for style heuristics.
- **Gap Identification**: The verified datasets are insufficient for the **full** analysis (FR-001, FR-002) as they lack the specific keyword filtering and code-style data needed for the LLM/Human classification heuristic.
- **Resolution**: The plan mandates **direct API querying** (FR-001) to fetch fresh PRs from high-star repositories that match the specific keywords. The verified HuggingFace datasets (PRS-v2-sample) will be used **only** for schema validation. The **CodeXGLUE/CodeParrot** dataset (or similar verified code-specific dataset) will be used to calibrate the style heuristics and provide the "Human-written baseline corpus" for FR-010.

**Conclusion**: The plan **cannot** rely solely on the verified HuggingFace PR datasets for the primary analysis. It must implement the GitHub REST API extraction logic described in FR-001 to obtain the specific subset of PRs required. The "Non-Disclosing" group is constructed as a negative control from the same repositories, acknowledging it may contain "Silent LLM" code.

## Methodology

### 1. Data Acquisition (FR-001, FR-007, FR-009)
- **Source**: GitHub REST API.
- **Target**: Repositories with ≥1000 stars.
- **Filter**: PR titles or commit messages containing "copilot", "llm", or "generated" (Disclosing Group).
- **Control**: Stratified sample of PRs from the *same* repositories that do *not* contain these keywords (Non-Disclosing Group).
- **Exclusion Rule (FR-009)**: If >50% of PRs in a repository contain the keywords, the repository is excluded to prevent selection bias.
- **Rate Limiting**: Token bucket algorithm (rate-limited to a defined threshold per hour). Exponential backoff (1s -> 60s).
- **Output**: Raw JSON/CSV in `data/raw/`.

### 2. Classification & Validation (FR-002, FR-008)
- **Primary Label**: Derived from keyword presence ("Disclosing" vs "Non-Disclosing"). This label represents the *disclosure status*, not the *code origin*.
- **Style Heuristics**:
 - `formatting_consistency`: Regex-based score for indentation/spacing uniformity.
 - `comment_density`: Ratio of comment lines to total lines.
 - **Calibration**: Heuristics are calibrated using the **CodeXGLUE/CodeParrot** dataset (human vs. LLM code examples) to establish baseline scores.
 - **Role**: Heuristics are used **only** as covariates in the regression model and for validation of the *disclosure signal* (e.g., identifying false positives where humans use keywords but write human-like code). They do **not** determine the primary group label.
- **Validation**: Manual review of 50 samples (stratified by label). Calculate Cohen's Kappa between the *keyword label* and *human-verified disclosure status*.
- **Sensitivity**: Sweep thresholds (0.6, 0.7, 0.8) to analyze false positive/negative rates of the *disclosure signal*.

### 3. Statistical Analysis (FR-004, FR-006, FR-010, Constitution Principle VII)
- **Outlier Removal**: Exclude PRs with review time < 0 or > 30 days.
- **Primary Test**: **Mann-Whitney U Test** (non-parametric) comparing review times (Disclosing vs. Non-Disclosing). α = 0.05. (Constitution Principle VII).
- **Multivariate Model**: Linear Mixed-Effects Regression with **SIMEX Correction**.
 - `Response`: `total_review_time` (minutes).
 - `Fixed Effects`: `origin_label` (Disclosing/Non-Disclosing), `code_size` (lines), `reviewer_count`, `reviewer_experience_proxy` (e.g., `reviewer_karma` or `contribution_count`).
 - `Random Effects`: `(1 | repository_id)`.
 - **SIMEX Protocol**:
 1. Estimate misclassification probability matrix from the manual validation set (error in the *disclosure* label).
 2. Simulate regression coefficients under increasing noise levels (λ = 0.5, 1.0, 1.5, 2.0).
 3. Extrapolate to λ = 0 (zero noise) to correct for attenuation bias.
 - **Matrix Correction (FR-010)**: If false positive rate > 5%, apply the SIMEX correction to the `origin_label` coefficient.
- **Slope Coefficients (SC-003)**: Extract and report the `code_size` slope coefficient separately for the "Disclosing" and "Non-Disclosing" groups (via interaction term or stratified models).
- **Assumption Checks**: Shapiro-Wilk test for normality of residuals.

### 4. Visualization (FR-005)
- Boxplot: Review time distribution by group.
- Scatter: Code size vs. Review time with regression lines (separate lines for each group).
- Residuals: Residuals vs. Predicted values.

## Limitations & Interpretation
- **Silent LLM Contamination**: The "Non-Disclosing" group is a negative control and may contain LLM-generated code that was not disclosed. The study measures the impact of *disclosure*, not the pure impact of *LLM code*. Any observed effect is attributed to the *signal* of disclosure.
- **Construct Validity**: The "Disclosing" group is defined by keywords, which may correlate with other factors (e.g., author experience, repository culture).
- **Heuristic Accuracy**: The style heuristics are calibrated on external code datasets but may not perfectly generalize to all PRs. The SIMEX correction aims to mitigate bias in the *disclosure* label.

## Compute Feasibility
- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - Data is processed in chunks.
 - No GPU models used (heuristic is regex/regex-based).
 - `statsmodels` and `scikit-learn` are CPU-optimized.
 - Sampling: If the API returns >10k PRs, random sampling will be applied to ensure <6h runtime and <7GB RAM usage.

