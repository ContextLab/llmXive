# Research: Evaluating the Impact of Code Generation on Code Review Quality

## Dataset Strategy

The study relies on a public GitHub Pull Request dataset. Based on the **Verified datasets** list provided in the project constraints, the primary candidate is:

| Dataset Name | Verified URL | Suitability & Fit Check |
|:--- |:--- |:--- |
| **prs-v2-sample** | ` | **Selected.** This dataset contains PR metadata, diffs, and review comments. It is the only verified source explicitly tagged as "PRs" with sufficient structure to extract code diffs and review text. **Critical Check**: Must contain `commit_message` field for heuristic classification. |
| **authors_merged_model_prs** | N/A | **Removed.** This dataset lacks specific review comment depth and sentiment fields required for SC-002. It is **not** a viable fallback. |
| **LLM-generated text datasets** | (Various HuggingFace links) | **Not Suitable.** These contain translation or general text, not GitHub PR code diffs, review comments, or merge timestamps. Cannot be used for this study. |

**Variable Fit Verification (Critical)**:
Before proceeding, the implementation MUST verify that `prs-v2-sample` contains the following fields:
1. `diff` or `patch`: Required for code complexity analysis (FR-003, FR-013).
2. `review_comments` or `comments`: Required for comment count and sentiment (FR-001, SC-002).
3. `created_at` / `merged_at`: Required for merge latency (SC-003).
4. `commit_message`: Required for LLM classification heuristics (FR-002).

*Constraint Note*: If the verified dataset lacks a specific variable (e.g., explicit "bug density" field), the pipeline will compute it via static analysis tools (radon/lizard) on the `diff` field. If the dataset lacks `review_comments` or `commit_message` entirely, the study cannot proceed and must halt (blocking flaw).

**Data Gap & Limitations**:
The "Verified datasets" list does not contain a dataset explicitly labeled as "LLM-generated code PRs" with ground truth labels. The plan relies on **heuristic classification** (keyword matching) as defined in FR-002. This introduces significant measurement error.
- **Impact**: False positives/negatives in the treatment variable.
- **Mitigation**:
 1. **Manual Audit**: A sample of PRs per group is audited to estimate the misclassification matrix.
 2. **SIMEX**: Simulation-Extrapolation is used to adjust the final effect sizes based on the audit matrix.
 3. **Framing**: All findings are explicitly framed as **associational**, not causal. The report includes a "Limitations" section detailing the measurement error risk.

## Statistical Methodology

### Causal DAG & Confounding
We model the relationships as follows:
- **LLM Usage** -> **Code Complexity** (Mediator)
- **LLM Usage** -> **Review Metrics** (Outcome)
- **Code Complexity** -> **Review Metrics** (Mediator)
- **Repo Size/Language** -> **LLM Usage** (Confounder)
- **Repo Size/Language** -> **Review Metrics** (Confounder)

**Decision**: Code Complexity is a **mediator**, not a confounder.
- **Action**: We **do NOT** use PSM to control for Code Complexity. Controlling for a mediator induces **over-control bias**, blocking the path through which LLMs might affect review quality.
- **Action**: PSM is used *only* for observed confounders (e.g., repository size, language, author experience) if available in the dataset.
- **Fallback**: If confounders are unavailable, we stratify by these variables or report descriptive statistics with caveats.

### Primary Analysis
- **Test 1 (Comment Count)**: Mann-Whitney U Test (Non-parametric).
 - *Rationale*: Non-normal distribution.
- **Test 2 (Sentiment Score)**: Mann-Whitney U Test.
 - *Contingency*: If correlation with bug density > 0.5, the result is **flagged** as a potential confounder and reported with a caveat, not excluded (FR-016).
- **Test 3 (Merge Latency)**: **Cox Proportional Hazards Model**.
 - *Rationale*: Merge latency is a time-to-event variable subject to censoring (PRs never merged). Mann-Whitney U is inappropriate for censored data.
 - *Model*: `h(t) = h0(t) * exp(beta * Group + beta_cov * Covariates)`.
- **Correction**: Benjamini-Hochberg (FDR) for family-wise error rate control (FR-005, SC-004).
- **Covariate Control**: PSM (or Exact Matching on Bins) for observed confounders (Repo Size, Language). **Not** for Code Complexity.

### Heuristic Robustness (SIMEX)
1. **Audit**: Manually label a representative sample of PRs per group to estimate sensitivity (True Positive Rate) and specificity (True Negative Rate) of the keyword heuristic.
2. **Matrix**: Construct the misclassification matrix $M$.
3. **Correction**: Apply SIMEX to the estimated coefficients ($\beta$) from the statistical tests to correct for attenuation bias caused by measurement error in the treatment variable.
4. **Output**: Report both raw and SIMEX-corrected effect sizes.

### Power & Sample Size
- **Target**: ≥1,000 PRs (500 LLM, 500 Human) **before** matching.
- **Matching Attrition**: Expect a substantial drop post-PSM. Target a substantial number of PRs in the matched sample.
- **Power Analysis**: Document minimum detectable effect size (Cohen's d) for 80% power at α=0.05 **on the matched sample**. If the matched sample is <200 per group, the study will report a power limitation.

### Observational Nature
- **Causal Claim**: None. All findings are framed as **associational** (FR-009, Assumption 5).
- **Confounding**: Acknowledge that LLM usage is not randomized. PSM/Stratification is the primary defense for observed confounders. Unobserved confounding remains a limitation.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (multiple CPU, 7 GB RAM, No GPU).
- **Constraints**:
 - **Memory**: Data subset to a representative sample size. Static analysis (radon) is memory-intensive; will process files in batches.
 - **Time**: Total runtime ≤6 hours.
 - **Libraries**: `scikit-learn`, `scipy`, `pandas`, `lifelines` (CPU-optimized). No GPU-specific libraries.
 - **Sentiment**: `textblob` is CPU-only and lightweight.
 - **Static Analysis**: `radon` and `lizard` are CPU-only.

## Risk Mitigation

| Risk | Mitigation Strategy |
|:--- |:--- |
| **Dataset Variable Mismatch** | Pre-flight check in `data/download.py` to verify schema. If missing critical fields, halt with error. |
| **Insufficient LLM Samples** | If <500 LLM-labeled PRs found, expand keyword list. If still <500, report "Insufficient Power" and stop. |
| **Heuristic Accuracy <70%** | Manual audit (FR-015) triggers halt. Heuristics are refined or study is aborted. |
| **Collinearity (VIF > 5)** | Switch to Exact Matching on Discrete Bins (a discrete set of bins for LOC/Complexity). |
| **Runtime Exceeds 6h** | Implement sampling (e.g., process every 2nd PR) if full dataset is too large. |
| **Censoring in Merge Latency** | Use Cox PH model instead of Mann-Whitney U. |
| **Measurement Error** | Apply SIMEX correction to effect sizes. |

## References

- **Dataset**: `prs-v2-sample` (HuggingFace). URL: `
- **Statistical Methods**: Mann-Whitney U, Benjamini-Hochberg, Cox PH, SIMEX.
- **Tools**: `radon` (Cyclomatic Complexity), `textblob` (Sentiment), `lifelines` (Survival Analysis).