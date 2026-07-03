---
action_items:
- id: 7b9eb8e74630
  severity: science
  text: "Report confidence intervals or standard errors for the accuracy gains (\u0394\
    Acc.) in Table 1. With N=830 (BrowseComp-Plus), a 1.1% drop (Tongyi-DeepResearch)\
    \ may not be statistically significant without variance estimates."
- id: c9b72e2b1bc8
  severity: science
  text: Clarify the statistical test used to validate the 'U-shaped' attention patterns
    in Section 5.2.1. Specify the null hypothesis and p-values for the claim that
    middle-turn attention is significantly lower than periphery attention.
- id: 42ca426efd6c
  severity: science
  text: The regression probe (Section 5.2.2) reports AUC scores (e.g., 0.74) but lacks
    significance testing against a random baseline or confidence intervals for the
    AUC estimates. Add these to support the claim of 'separability'.
- id: c7b7316622ee
  severity: science
  text: The human audit agreement rate is stated as >99.9% (Appendix E001) based on
    a 15% sample. Report the exact sample size (N) and the 95% confidence interval
    for this agreement rate to assess the reliability of the LLM-as-Judge metric.
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T02:33:21.863361Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is generally robust in its experimental design, covering a wide range of model sizes and retrievers. However, several key statistical claims lack necessary measures of uncertainty or formal hypothesis testing, which is critical for interpreting the "regime map" boundaries.

First, **Table 1** presents point estimates for accuracy gains (ΔAcc.) but omits measures of variance (e.g., standard error, 95% confidence intervals). Given the sample sizes (e.g., N=830 for BrowseComp-Plus), small differences such as the -1.1% drop for Tongyi-DeepResearch or the +0.1% gain for GPT-OSS-120B may not be statistically distinguishable from zero. Without confidence intervals, the claim of a "sharp collapse" in the saturated regime is difficult to validate statistically. The authors should report bootstrapped confidence intervals for the accuracy differences to confirm the significance of the regime boundaries.

Second, the **attention analysis** in Section 5.2.1 claims a "U-shaped" pattern and states that attention to middle observations is "significantly lower." The text references Figure 5 but does not specify the statistical test used (e.g., paired t-test, ANOVA) to compare attention weights across turn positions. The claim of "significance" requires a reported p-value or effect size to be scientifically rigorous.

Third, the **regression probe** results in Section 5.2.2 rely on AUC scores (e.g., 0.74) to argue for "separability" of rescue cases. While AUC is a useful metric, the paper does not provide confidence intervals for these AUC estimates or a statistical test comparing them against a null model (e.g., random guessing). The distinction between "partially separable" and "highly separable" regimes needs statistical backing beyond point estimates.

Finally, the **human audit** validation (Appendix E001) reports a >99.9% agreement rate based on a 15% sample. The exact number of samples (N) and the 95% confidence interval for this agreement rate should be provided to assess the precision of the LLM-as-Judge evaluation metric.

Addressing these points by adding confidence intervals, p-values, and sample sizes will significantly strengthen the statistical validity of the paper's conclusions.
