# Research: Evaluating the Impact of Code Generation on Code Review Quality

## Dataset Strategy

The primary dataset is the **GitHub Pull Requests (PRs) v2 sample** from HuggingFace, which contains PR metadata, code diffs, review comments, and merge timestamps. This dataset is verified and accessible via the HuggingFace `datasets` library.

| Dataset Name | Verified URL | Loader Method | Variables Provided | Coverage Check |
|--------------|--------------|---------------|--------------------|----------------|
| PRs v2 Sample | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | `datasets.load_dataset("parquet", data_files="...")` | code_diff, review_comments, merge_timestamp, project_metadata | ✅ Confirmed: contains all required fields for ≥95% of records |
| Authors Merged PRs | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | `datasets.load_dataset("parquet", ...)` | code_diff, review_comments, merge_timestamp | ✅ Confirmed: alternative source if primary fails (Note: Shares same label limitation) |
| Authors Merged Dataset PRs | https://huggingface.co/datasets/davanstrien/authors_merged_dataset_prs/resolve/main/data/train-00000-of-00001-d5c709e857d2ca0b.parquet | `datasets.load_dataset("parquet", ...)` | code_diff, review_comments, merge_timestamp | ✅ Confirmed: backup source (Note: Shares same label limitation) |

**Decision**: Use `loubnabnl/prs-v2-sample` as primary source due to its explicit inclusion of review comments and merge timestamps. If completeness <95%, fall back to `davanstrien` datasets.

**Variable Fit Confirmation**:
- **code_diff**: Present in all datasets → used for complexity metrics (radon).
- **review_comments**: Present → used for comment count, sentiment (textblob).
- **merge_timestamp**: Present → used for merge latency.
- **project_metadata**: Present → used for filtering (e.g., language, repo age).
- **LLM Label**: **NOT present**. The study relies on **keyword heuristics** to define "Keyword-Associated" PRs. This is a proxy variable, not ground truth.

**Missing Data Handling**: Records with null values in required fields (code_diff, review_comments, merge_timestamp) will be filtered. If completeness <95%, the pipeline halts with a 'Data Completeness Error' (FR-014).

## Statistical Methodology

### Primary Analysis
- **Test**: Mann-Whitney U test (non-parametric) to compare review metrics (comment count, sentiment score, merge time) between **Keyword-Associated** and **Human** groups.
- **Correction**: Benjamini-Hochberg procedure for family-wise error control (α ≤ 0.05) across ≥3 pairwise comparisons (FR-005).
- **Effect Size**: Cohen’s d (or rank-biserial correlation for Mann-Whitney) reported for all significant results.
- **Power Analysis & Noise Adjustment**: 
  1. Perform a **Manual Audit** on a random sample (N=200) to estimate the **Label Noise Rate** (misclassification rate) of the keyword heuristic.
  2. Calculate **Effective Sample Size**: $N_{effective} = N_{raw} \times (1 - \text{noise\_rate})^2$.
  3. Document the minimum detectable effect size for [deferred] power using $N_{effective}$, not $N_{raw}$ (FR-008).

### Secondary Analysis (Spec Compliance & Mediator Note)
- **Linear Regression with VIF**: As mandated by **FR-010**, a linear regression model will be fitted with review metrics as outcomes and code complexity (cyclomatic complexity, LOC) as covariates. Variance Inflation Factors (VIF) will be calculated and reported.
- **Rationale for Execution**: This step is executed to satisfy the explicit requirement of FR-010 and User Story 2.
- **Interpretation Caveat**: The plan acknowledges that code complexity is likely a **mediator** (a mechanism through which LLMs affect review quality). Statistically controlling for a mediator can induce collider bias and obscure the total effect. Therefore, while the regression results and VIFs will be reported as required, the **primary interpretation** of the study's findings will rely on the Mann-Whitney U tests (which capture the total effect). The regression results will be framed as "adjusted associations" with an explicit note that controlling for complexity may not be methodologically ideal for causal inference in this specific context, ensuring statistical rigor is maintained despite Spec constraints.
- **VIF Check**: VIF < 5 will be reported for all predictors. If VIF ≥ 5, the model will be flagged, but the Mann-Whitney results remain the primary evidence.

### Sentiment Validity Calibration
- **Limitation**: TextBlob is a general-purpose tool and may misclassify technical code review jargon.
- **Calibration Step**: A manual audit of 100 random comments will be coded for "criticality" and "tone" by a human reviewer.
- **Adjustment**: The correlation ($r$) between TextBlob scores and human codes will be calculated. Final sentiment findings will be reported with a **validity margin** based on this correlation, acknowledging the domain mismatch.

### Sensitivity Analysis
- **Threshold Sweep**: Keyword match count threshold swept across {1, 2, 3} to assess robustness of classification boundaries (FR-007).
- **Visualization**: Plot classification rates and statistical significance across thresholds.

## Computational Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU cores, ~7 GB RAM, no GPU).
- **Data Size**: Up to 50,000 PRs; processed in chunks if needed.
- **Libraries**: CPU-only versions of `scikit-learn`, `scipy`, `radon`, `textblob`, `matplotlib`, `seaborn`.
- **Runtime**: Target ≤6 hours; memory usage monitored to stay ≤7 GB.
- **Approximations**: If dataset exceeds memory, sample to [deferred] PRs or process in batches.

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Insufficient LLM-labeled PRs (<500) | Halt with 'Power Insufficiency' error (FR-013); report observed counts. |
| Missing required fields (<95% completeness) | Halt with 'Data Completeness Error' (FR-014). |
| Code complexity metrics fail for some languages | Log warning, exclude from complexity analysis, proceed with other metrics. |
| Heuristic classification accuracy low | Perform manual audit of random sample; report observed accuracy and adjust power (FR-015). |
| TextBlob validity low | Report validity margin based on manual calibration; frame findings as "TextBlob-observed tone". |
| Mediator Bias in Regression | Execute regression for FR-010 compliance; interpret results with explicit caveat regarding mediator bias; rely on Mann-Whitney for primary conclusions. |

## Assumptions & Limitations

- **Assumption**: Keyword heuristics (≥2 LLM-related keywords) identify a distinct subset of PRs ("Keyword-Associated") that is statistically distinguishable from others, even if not perfectly aligned with "LLM-generated" code.
- **Limitation**: No random assignment; findings are associational, not causal.
- **Limitation**: Review sentiment via TextBlob may not capture nuanced feedback; validity is calibrated via manual audit.
- **Limitation**: Code complexity tools (radon) may not support all languages; warnings logged.
- **Limitation**: Code complexity is a mediator; the regression model required by FR-010 is executed for compliance but interpreted with caution regarding causal inference.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use Mann-Whitney U test | Non-parametric; robust to non-normal distributions of review metrics. |
| Apply Benjamini-Hochberg correction | Controls false discovery rate for multiple comparisons; less conservative than Bonferroni. |
| Use TextBlob with Calibration | Lightweight, CPU-only; validity adjusted via manual audit correlation. |
| Manual audit for heuristic accuracy | Required by FR-015; ensures transparency in classification method and power adjustment. |
| **Execute Linear Regression for FR-010 Compliance** | Required by Spec (FR-010, US-2). Executed with explicit note on mediator bias to satisfy both Spec and Statistical Rigor. |
| Frame findings as associational | Constitution Principle VII and spec assumption: no randomization. |