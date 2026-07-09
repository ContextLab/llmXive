# Research: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## 1. Problem Definition & Research Question

**Primary Question**: Does code associated with LLM generation tags exhibit different long-term maintainability characteristics compared to human-written code, as measured by code churn, bug fix latency, and structural complexity metrics over a six-month observation window?

**Hypotheses**:
- **H1**: LLM-tagged code has higher code churn (lines added/deleted) than human-written code.
- **H2**: LLM-tagged code has longer bug fix latency than human-written code.
- **H0**: No significant difference exists between LLM and Human code in maintainability metrics.

**Scope**: Python and JavaScript repositories; 6-month observation window; 1:1 matched pairs.

## 2. Dataset Strategy

### 2.1 Primary Data Source: Live GitHub API
The spec requires **longitudinal data** (6-month history, bug fix latency, code churn) for **specific code blocks** tagged as LLM/Human. No static dataset in the "Verified datasets" block contains this specific combination of:
- Code blocks with origin labels (LLM/Human)
- Associated git history spanning 6 months
- Linked issue/PR data for bug fix latency

**Decision**: The primary data source is the **GitHub Search API** and **Git Log API**, accessed dynamically. This satisfies FR-001 (identify 50-100 repos) and FR-004 (extract longitudinal metrics).

**Dataset Construction Steps**:
1. **Repo Identification**: Search GitHub for `topic:llm-generated` or `topic:copilot`. If < 50, expand to keywords.
2. **Code Block Extraction**: Clone repos (shallow depth 100). Extract functions/classes.
3. **Labeling**: Run CodeBERT (ONNX) on each block. Tag if confidence ≥ 0.8.
4. **Longitudinal Tracking**: For each tagged block, track changes in `git log` over 6 months.
5. **Issue Linking**: Match commits to issues via "Fixes #N" patterns.

### 2.2 Verified Datasets (Auxiliary Only)
The following datasets are **verified** but **insufficient** for the primary analysis due to lack of longitudinal maintenance data. They may be used for:
- **Auxiliary Analysis**: Testing classifier performance on static text.
- **Fallback**: If live API fails, use for a cross-sectional snapshot (not longitudinal).

| Dataset Name | Verified URL | Usage in Plan | Limitation |
|--------------|--------------|---------------|------------|
| LLM-generated (parquet) | ` | Classifier validation (static) | No git history, no bug fixes, no human/LLM pairs. |
| JavaScript (parquet) | ` | Classifier validation (static) | No longitudinal data, no origin labels. |
| ONNX configs | ` | Model config reference | Not a code dataset. |

**Critical Note**: The plan **does not** use these datasets for the main analysis (FR-001 to FR-005). They are cited only to acknowledge the lack of a pre-packaged longitudinal dataset and to justify the live API approach.

### 2.3 Ground Truth Verification
- **Method**: Randomly select a sufficient number of blocks from the tagged set.
- **Action**: Manual review by human expert.
- **Storage**: `data/ground_truth/manual_labels.csv`. **This file is checksummed immediately upon creation and recorded in `state/` as a versioned artifact.**
- **Metric**: Precision/Recall of CodeBERT against ground truth (FR-007). **This metric is used to drive the Sensitivity Analysis.**

## 3. Methodology & Statistical Rigor

### 3.1 Data Preprocessing & Matching
1. **Filtering**: Exclude repos with < 5 LLM and < 5 Human blocks.
2. **Exclusion**: Blocks with classifier confidence < 0.8 are excluded.
3. **Collinearity Check**: Before matching, verify that classifier confidence is not highly correlated with complexity metrics. If correlated, restrict matching to blocks with neutral confidence to avoid matching on the "LLM-ness" itself.
4. **Matching**: 1:1 nearest-neighbor propensity score matching (FR-008).
 - **Covariates**: Cyclomatic complexity, Nesting depth, Lines of Code (LOC), **AND Repository-level covariates** (Stars, Repo Age, Contributor Count).
 - **Stratification**: Matching is performed **within** repositories where possible to control for "confounding by repository."
 - **Algorithm**: `sklearn.neighbors.NearestNeighbors` with Euclidean distance on normalized scores.
 - **Balance Check**: Standardized mean difference < 0.1 post-matching.

### 3.2 Metric Extraction & Bias Mitigation
- **Code Churn**: Sum of lines added/deleted in `git log` for the block's file path over 6 months.
- **Bug Fix Latency**: Time between commit with "Fixes #N" and issue closure.
 - **Survivorship Bias Mitigation**: We acknowledge that only "fixable" code with linked issues is measured. We perform a **Linking Bias Analysis**: compare the proportion of LLM vs. Human blocks that have linked issues. If significant, we stratify the latency analysis or explicitly qualify results as "for tracked issues only."
 - **Handling Nulls**: Pairs with null latency in either block are excluded from the latency analysis (but retained for churn).

### 3.3 Statistical Analysis (LMM)
- **Model**: Linear Mixed-Effects Model (LMM) using `statsmodels` or `lme4`.
- **Formula**: `metric ~ origin_label + (1 | repo_id)`
 - `origin_label`: Fixed effect (LLM vs. Human).
 - `repo_id`: Random intercept to account for non-independence of blocks within the same repository.
- **Correction**: Benjamini-Hochberg (FDR) for multiple comparisons (churn, latency).
- **Effect Size**: Marginal R-squared and Cohen's d (calculated from fixed effects).
- **Sensitivity Analysis**:
 - **Input**: Misclassification rates from Ground Truth (Precision/Recall).
 - **Action**: Adjust the observed effect size to account for measurement error using standard correction formulas. Report the "bias-corrected" effect size and its confidence interval.
 - **Purpose**: Quantify how much the classifier uncertainty might inflate or deflate the true effect.

### 3.4 Computational Feasibility
- **Environment**: GitHub Actions free-tier (limited CPU, 7GB RAM, 6h limit).
- **Optimizations**:
 - **Shallow Clones**: `--depth 100` to reduce disk/memory.
 - **ONNX Runtime**: CPU-optimized inference for CodeBERT.
 - **Sampling**: Process a representative subset of repositories; if performance constraints arise, reduce the subset size.
 - **Memory**: Stream git logs; avoid loading full history.
- **Fallback**: If a repo is deleted (404), exclude gracefully.

## 4. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **API Rate Limits** | Implement exponential backoff; cache responses; use `requests` session. |
| **Classifier Inaccuracy** | Ground truth verification; **Sensitivity Analysis** to bound bias. |
| **Missing Issue Links** | **Linking Bias Analysis**; exclude pairs from latency analysis; retain for churn. |
| **Repo Deletion** | Graceful 404 handling; exclude from final count. |
| **Power Limitations** | Post-hoc analysis; report if power < 0.80. |
| **Memory Overflow** | Stream processing; limit repo count; sample if needed. |
| **Statistical Invalidity** | Use LMM instead of Wilcoxon to handle clustering. |

## 5. Decision Rationale

- **Why Live API?**: No existing dataset contains longitudinal maintenance data for LLM vs. Human code. Static datasets (verified URLs) lack the required temporal dimension.
- **Why CodeBERT (ONNX)?**: Balances accuracy and CPU performance. `transformers` + PyTorch is too slow for 6-hour limit.
- **Why LMM?**: The data is hierarchical (blocks within repos). Wilcoxon assumes independence. LMM with random effects for `repo_id` is the scientifically sound choice to avoid false positives.
- **Why FDR Correction?**: Multiple hypothesis tests (churn, latency) require family-wise error control.
- **Why Sensitivity Analysis?**: To address the circular validation risk and quantify the impact of classifier uncertainty on the final conclusions.

## 6. Open Questions

- **Q1**: What is the exact distribution of LLM vs. Human blocks in the target repos? (Answer: Empirical, from live API).
- **Q2**: How many repos are needed to achieve adequate statistical power? (Answer: Post-hoc analysis).
- **Q3**: Are there systematic biases in the "topic:llm-generated" tag? (Answer: Mitigated by manual verification and linking bias analysis).
