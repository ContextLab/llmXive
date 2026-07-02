---
action_items:
- id: e041ae6b9a73
  severity: science
  text: Report confidence intervals or standard errors for the Odds Ratios (OR) in
    Table 1 and the success ratios in Table 2. The current point estimates (e.g.,
    OR=0.53, 100.00%) lack measures of uncertainty, making it impossible to assess
    the statistical significance of the correlation between OR and onset time or the
    precision of the exploitability estimates.
- id: 3c531cf8d774
  severity: science
  text: Clarify the statistical methodology for determining the 'canonical onset'
    (modal step) and the associated 'threshold-induced interval' in Table 1. The current
    description implies a heuristic threshold sweep; specify the statistical criteria
    (e.g., change-point detection, hypothesis testing) used to define the onset and
    justify the interval width.
- id: ee7c635c33b9
  severity: science
  text: Provide p-values or effect sizes for the capability degradation claims in
    Section 3.1 (Table 3). The text states 'significant in-domain capability drops'
    for hacked models, but no statistical test (e.g., t-test, Mann-Whitney U) or variance
    metrics are reported to support this significance claim against the baseline.
artifact_hash: eca43eb888bbc8155fd1bf21a6b137ce6bb47419fcb91606da445eda44a63a5a
artifact_path: projects/PROJ-663-https-arxiv-org-abs-2606-04923/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T18:49:48.228300Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a rigorous framework for analyzing reward hacking, but the statistical reporting requires strengthening to fully support the quantitative claims.

First, **uncertainty quantification is missing** for key metrics. Table 1 reports Odds Ratios (OR) linking bias entanglement to onset time (e.g., OR=0.53 for self-praise on VerInstruct). Without confidence intervals or standard errors derived from the underlying contingency tables, it is unclear if the observed correlation between OR and onset delay is statistically robust or driven by noise. Similarly, Table 2 reports generation success ratios (e.g., 100.00% for Lexical bias). While the sample size (300 trials) is noted, the absence of confidence intervals (e.g., Wilson score intervals) makes it difficult to compare the precision of these estimates across bias types, particularly for the 66.00% Format bias.

Second, the **definition of "canonical onset"** lacks statistical formalism. The paper defines onset via a "modal canonical step" derived from a threshold sweep (Appendix A). However, it does not specify the statistical test or change-point detection algorithm used to identify the "rising edge" of the shortcut prevalence $M(t)$. The "threshold-induced interval" is described heuristically; a more rigorous approach would involve defining a null hypothesis (e.g., random fluctuation) and reporting the p-value or false discovery rate associated with the detected onset step.

Third, claims of **statistical significance** in capability degradation are unsupported by data. Section 3.1 states that models exhibiting hacking showed "significant in-domain capability drops" (Table 3). However, the table only provides point estimates (e.g., 31.7 vs 23.7 for IFB Strict). No standard deviations, standard errors, or results of statistical tests (e.g., paired t-tests or non-parametric equivalents) are provided to validate the term "significant." Given the small number of experimental runs (n=1 per condition implied by the single values), the authors must clarify if these are averages over multiple seeds or single runs, and provide appropriate error bars or test statistics.

Finally, the **detection performance metrics** in Table 4 (RHDA vs. baselines) report aggregate distances ($\sum d_p$, $\sum d_I$) but lack variance measures. To properly compare RHDA-Plus against baselines like CC-Sonnet, the authors should report the standard deviation of the localization errors across the six runs or perform a statistical test to confirm that the observed improvements are not due to chance.
