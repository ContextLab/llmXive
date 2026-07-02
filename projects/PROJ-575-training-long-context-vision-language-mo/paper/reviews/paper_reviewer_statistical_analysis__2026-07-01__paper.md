---
action_items:
- id: ffb202e009c6
  severity: science
  text: The paper reports performance gains (e.g., +7.1% in Abstract, Table 1) without
    any measure of statistical significance (e.g., standard deviation, confidence
    intervals, or p-values). Given the use of LLM-based judges which can introduce
    variance, single-run results are insufficient to claim superiority. Re-run experiments
    with multiple seeds or report variance metrics.
- id: 47c0ab3d7dd1
  severity: science
  text: In Section 5.2 (Table 2), the optimal extraction-to-reasoning ratio (8:2)
    is selected based on point estimates. No statistical test (e.g., t-test or ANOVA)
    is provided to confirm that the difference between 8:2 and the next best ratio
    (6:4) is significant rather than noise. The conclusion that 'retrieval remains
    the primary bottleneck' relies on this unverified difference.
- id: b1ca88592bf7
  severity: science
  text: The claim that 'pure long-document VQA largely preserves short-context capabilities'
    (Section 5.3) compares a 0% short-data model (65.48) to the base (66.47). The
    drop is small, but without error bars or multiple runs, it is impossible to determine
    if this preservation is statistically robust or if the observed 'mild drop' is
    within the margin of error of the evaluation protocol.
- id: fe6ba9965f13
  severity: science
  text: The evaluation relies heavily on LLM-based judges (Appendix A.2) for scoring.
    The paper does not report the inter-annotator agreement (e.g., Cohen's Kappa)
    or the stability of the judge itself. If the judge has high variance, the reported
    gains (e.g., 57.70 vs 50.59) may not be reproducible. A statistical analysis of
    the judge's consistency is required.
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:41:56.096100Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the experimental analysis is currently insufficient to support the paper's central claims regarding the superiority of specific data mixtures and the preservation of capabilities.

First, the paper presents results as deterministic point estimates derived from single training runs (e.g., Table 1, Table 2, Table 3). In deep learning, particularly with stochastic optimizers and LLM-based evaluation judges, results exhibit inherent variance. The claim that the 8:2 extraction-to-reasoning ratio is optimal (Section 5.2) is based on a marginal difference (57.70 vs 57.27) which may not be statistically significant. Without reporting standard deviations across multiple random seeds or conducting hypothesis tests (e.g., paired t-tests), it is impossible to distinguish genuine methodological improvements from random noise.

Second, the evaluation methodology relies on LLM judges (Appendix A.2) to score answers. The paper fails to quantify the reliability of this metric. There is no report on the variance of the judge itself, inter-judge agreement, or confidence intervals for the reported scores. If the judge's variance is high, the observed 7.1% improvement (Abstract) could be an artifact of the specific judge instance rather than a true model capability gain.

Third, the conclusion that "pure long-document VQA largely preserves short-context capabilities" (Section 5.3) compares a 0% short-data model (65.48) to the base (66.47). While the drop appears small, the lack of error bars makes this claim fragile. A statistical test is required to confirm that the difference between the 0% and 20% short-data settings is not significant, or that the 0% setting is not significantly worse than the base.

Finally, the generalization claims to 256K and 512K contexts (Section 6.2) are based on single evaluations. Given the extrapolation nature of these tests, the variance is likely higher than in the 128K setting. The paper must provide statistical evidence (e.g., confidence intervals) to support the assertion that the model "maintains strong performance" rather than just "performing better than a failing baseline."

To proceed, the authors must re-run key ablation studies (specifically the data mixture and length distribution experiments) with at least 3 random seeds, report mean and standard deviation, and perform statistical significance testing on the reported improvements. Additionally, the stability of the LLM judge should be quantified.
