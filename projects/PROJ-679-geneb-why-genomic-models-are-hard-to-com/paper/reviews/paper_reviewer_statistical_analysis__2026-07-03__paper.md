---
action_items:
- id: 3e50e36a5cb0
  severity: science
  text: The paper reports Spearman correlations for scaling laws (e.g., Table 1) but
    omits confidence intervals. Given the n=40 sample size, CIs are essential to assess
    the precision of these estimates and the robustness of the 'significant' claims,
    particularly for categories with p-values near 0.05 (e.g., Species Classification
    p=0.057).
- id: 825d424e57e4
  severity: science
  text: The controlled pair comparisons (n=6 for human vs. multi-species) rely on
    small sample sizes to draw broad conclusions about pretraining corpus effects.
    The manuscript should report the variance (e.g., standard error or 95% CI) of
    the mean delta-MCC to demonstrate that the observed effects are not driven by
    outliers or high variance within the pairs.
- id: 4cca19bcc448
  severity: science
  text: The analysis of few-shot degradation (Figure 3) presents mean MCC drops but
    lacks statistical testing for the 'inverse performance pattern' claim. A formal
    test (e.g., correlation between full-shot performance and degradation magnitude)
    with a p-value and confidence interval is required to support the assertion that
    smaller drops occur in weaker models.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:09:33.294033Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in GENEB is generally rigorous, employing appropriate metrics (MCC) and robust evaluation protocols (5 seeds, logistic regression). The use of Spearman rank correlation to assess scaling laws is suitable for the non-linear relationship between parameter count and performance. However, the manuscript relies heavily on point estimates without providing measures of uncertainty, which weakens the statistical support for several key claims.

First, the correlation analyses in Table 1 (Per-category scaling correlations) report p-values but omit confidence intervals for the Spearman $\rho$ coefficients. With a sample size of $n=40$, the confidence intervals for correlations near the significance threshold (e.g., Species Classification, $p=0.057$) are likely wide. Reporting 95% CIs would clarify whether the lack of significance is due to low power or a genuinely weak relationship.

Second, the "Controlled-Pair Comparisons" (Appendix, Section 30 pairs) aggregate results from very small subsets (e.g., $n=6$ pairs for human vs. multi-species). While the mean $\Delta$ MCC is reported, the absence of standard errors or confidence intervals makes it difficult to assess the reliability of these differences. For instance, the claim that multi-species pretraining yields a $+0.012$ aggregate advantage relies on averaging only 6 pairs; a single outlier pair could significantly alter this conclusion.

Third, the "inverse performance pattern" in few-shot robustness (Section 4, paragraph 4) asserts that weaker models degrade less. This is a correlation claim (performance vs. degradation) that requires a statistical test (e.g., Pearson/Spearman correlation with p-value and CI) rather than just a descriptive list of the top 5 models. Without this, the pattern remains anecdotal.

Finally, the probe stability analysis (Appendix) correctly uses rank correlation to show robustness, but the absolute MCC shifts (mean $+0.011$) should be accompanied by a distribution (e.g., boxplot or range) to ensure the "small" shifts are not masking large variances in specific tasks. Overall, adding confidence intervals and formal significance tests for the comparative claims would significantly strengthen the statistical validity of the paper.
