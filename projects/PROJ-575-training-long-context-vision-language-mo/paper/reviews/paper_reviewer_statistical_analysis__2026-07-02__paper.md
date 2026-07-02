---
action_items:
- id: 9e9c3759b57d
  severity: science
  text: The paper reports performance gains (e.g., +7.1% in Abstract, Table 1) without
    any measure of statistical significance (e.g., standard deviation, confidence
    intervals, or p-values). Given the use of LLM-based judges which can be stochastic,
    single-run results are insufficient to claim superiority. Re-run experiments with
    multiple seeds or report variance.
- id: 0146582bac36
  severity: science
  text: In Section 5.2 (Table 2), the selection of the 8:2 extraction-to-reasoning
    ratio is based on a single point estimate. The difference between 8:2 (57.70)
    and 6:4 (57.27) is marginal (0.43 points). Without statistical testing or error
    bars, it is unclear if this difference is meaningful or due to noise. Justify
    the choice statistically or acknowledge the uncertainty.
- id: 16b0e8470aa4
  severity: science
  text: The ablation on mRoPE base frequency (Appendix C.3, Table 12) shows conflicting
    trends across tasks (e.g., 8e6 improves MMLB-D but degrades reasoning). The paper
    lacks a statistical aggregation method (e.g., ANOVA or paired t-tests) to determine
    if the observed differences are significant across the three tasks. A more rigorous
    analysis of the trade-offs is required.
- id: 66d828d53504
  severity: science
  text: The claim that 'pure long-document VQA largely preserves short-context capabilities'
    (Section 5.3) relies on a drop from 66.47 to 65.48 (0.99 points). Without reporting
    the standard error of the mean across the six benchmarks or a significance test,
    this claim of 'preservation' is statistically weak. Provide variance metrics for
    the short-context benchmarks.
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:46:16.290258Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis presented in this paper is insufficient to support the strong claims made regarding the superiority of the proposed training recipes and the significance of the observed performance gains.

First, the paper consistently reports single-point performance metrics (e.g., accuracy scores in Tables 1, 2, and 3) without any measure of variance, such as standard deviation, standard error, or confidence intervals. In the context of Large Vision-Language Models (LVLMs), evaluation often involves LLM-based judges (as noted in Appendix B.1), which can introduce stochasticity. Without multiple runs (different random seeds) or bootstrapping, it is impossible to determine if the reported improvements (e.g., the 7.1% gain in the Abstract or the 0.43% difference between 8:2 and 6:2 ratios in Table 2) are statistically significant or merely artifacts of random initialization or evaluation noise.

Second, the selection of hyperparameters and data mixtures lacks statistical rigor. For instance, in Section 5.2, the authors choose an 8:2 extraction-to-reasoning ratio because it yields the highest average score. However, the difference between the 8:2 (57.70) and 6:4 (57.27) configurations is minimal. Without a statistical test (e.g., a paired t-test or ANOVA) to confirm that this difference is significant, the choice appears arbitrary. Similarly, the ablation on mRoPE base frequency in Appendix C.3 shows inconsistent results across different tasks (e.g., 8e6 improves one metric but hurts another), yet the paper concludes that "moderate scaling is sufficient" without a statistical aggregation of these effects.

Finally, the claim that short-context capabilities are "largely preserved" (Section 5.3) is based on a small absolute drop (0.99 points) without reporting the variance across the six short-context benchmarks. To robustly support the conclusion that the model does not suffer catastrophic forgetting, the authors must provide statistical evidence that the performance drop is not significant or is within the margin of error.

I recommend a full revision where the authors re-run key experiments with multiple seeds to report mean and standard deviation, and apply appropriate statistical tests to validate the significance of their ablation studies and final comparisons.
