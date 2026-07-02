---
action_items:
- id: bf18d5264690
  severity: science
  text: Section 5.3 states metrics are 'macro-averaged across instances' but does
    not report confidence intervals or standard errors for the main results in Table
    1. Given the small sample size in the Repository setting (20 instances), statistical
    significance testing (e.g., paired t-tests or Wilcoxon signed-rank) is required
    to validate the claimed gains over baselines.
- id: 2b8dfd6b7c4b
  severity: science
  text: The LLM judge (GPT-5 mini) is used for Identification and Resolution scoring
    (Section 5.3). The paper lacks an inter-rater reliability analysis (e.g., Cohen's
    Kappa) or a human-in-the-loop validation study to establish the validity and consistency
    of these automated metrics, which are central to the paper's conclusions.
- id: 1b583210610b
  severity: science
  text: Figure 3 (budget_scaling) and Figure 5 (template_count_scaling) show performance
    trends but lack error bars or confidence intervals. Without these, it is impossible
    to determine if the observed scaling effects are statistically significant or
    within the noise of the evaluation process.
artifact_hash: ba0baa17db4681e44851057971abf7e28abd129eef36849b4fb4fc0aac6085dd
artifact_path: projects/PROJ-669-tide-proactive-multi-problem-discovery-v/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:08:18.758737Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally sound in its design of comparing TIDE against baselines, but it lacks necessary rigor in reporting uncertainty and validating the evaluation metrics.

First, the sample sizes for the evaluation splits are relatively small, particularly for the Software Repository setting (20 instances, Section 5.1). While the authors report mean Coverage and F1 scores in Table 1, they do not provide confidence intervals, standard deviations, or results of statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) to confirm that the observed improvements over baselines are not due to random variance. Given the high variance often seen in LLM-based evaluations, reporting these statistics is essential to support the claim that TIDE "consistently outperforms" baselines.

Second, the reliance on an LLM judge (GPT-5 mini) for scoring Identification and Resolution (Section 5.3) introduces a potential source of bias and inconsistency that is not quantified. The paper does not report inter-rater reliability metrics (such as Cohen's Kappa) between the LLM judge and human annotators, nor does it provide a validation study demonstrating the judge's consistency across different prompts or instances. Without this validation, the absolute scores and the magnitude of the gains reported in Table 1 are difficult to interpret with confidence.

Finally, the scaling analyses presented in Figure 3 (budget scaling) and Figure 5 (template pool size) lack error bars or confidence intervals. These figures are used to argue for the effectiveness of iterative discovery and template scaling, but without visual or statistical representation of variance, it is unclear if the observed trends are robust. The authors should re-run these experiments with multiple seeds or report the variance across the existing runs to substantiate these claims.
