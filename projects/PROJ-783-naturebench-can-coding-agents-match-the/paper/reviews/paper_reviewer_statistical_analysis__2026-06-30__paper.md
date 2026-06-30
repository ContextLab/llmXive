---
action_items:
- id: 82480de55ef7
  severity: science
  text: The paper reports aggregate success rates (e.g., 17.8% Surpass-SOTA) without
    confidence intervals or standard errors. Given the small sample size (N=90 tasks)
    and the binary nature of the outcome, the variance is high. A binomial proportion
    confidence interval (e.g., Wilson score interval) must be calculated and reported
    for all main results in Table 1 to establish statistical significance of the differences
    between models.
- id: 663788dc0ac8
  severity: science
  text: The analysis of failure modes (e.g., 'wrong method choice 45.1%') treats the
    90 tasks as independent observations. However, tasks are clustered within 6 domains.
    The paper fails to account for this hierarchical structure. A mixed-effects model
    or a domain-stratified analysis is required to avoid pseudoreplication and inflated
    Type I error rates when attributing failure causes.
- id: a57ee2a77fa5
  severity: science
  text: The metric g (relative gap) is used to define 'Surpass-SOTA' (g > 0.1) and
    'Match-SOTA' (g >= 0). The paper does not report the distribution of g or the
    sensitivity of these thresholds to noise in the SOTA baselines. A sensitivity
    analysis varying the threshold (e.g., g > 0.05, g > 0.15) is needed to demonstrate
    the robustness of the primary claims.
- id: 2f5fcc4c8c53
  severity: science
  text: The cost analysis in Table 2 includes estimated token counts for third-party
    models (marked with *). The paper does not provide an error bound or validation
    method for these estimates. Since cost is a key variable in the 'insufficient
    compute budget' failure mode, the uncertainty in these estimates must be quantified
    to support the conclusion that budget was a limiting factor.
artifact_hash: a6c4bf4c6300b132fd82818749a0c8d087f9c694f2c1e50110083271605915a9
artifact_path: projects/PROJ-783-naturebench-can-coding-agents-match-the/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:47:15.953178Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the evaluation in NatureBench is currently insufficient to support the strong claims regarding agent capabilities and failure modes. The primary concern is the lack of uncertainty quantification. The main results table (Table 1) presents point estimates (e.g., 17.8% Surpass-SOTA for Claude Opus 4.7) derived from a sample of only 90 tasks. With such a small N, the standard error for a proportion near 0.18 is approximately 4%, meaning the 95% confidence interval is roughly [10%, 26%]. The paper fails to report these intervals, making it impossible to determine if the observed differences between models (e.g., 17.8% vs 15.6%) are statistically significant or merely noise.

Furthermore, the analysis of failure modes (Section 4) aggregates counts across all tasks without accounting for the hierarchical structure of the data. Tasks are nested within six distinct scientific domains (Protein, Cellular, etc.), which likely share underlying difficulty characteristics. Treating the 90 tasks as independent i.i.d. samples violates the assumption of independence required for simple frequency counts and chi-square tests. A mixed-effects logistic regression or a domain-stratified analysis is necessary to correctly attribute failure causes (e.g., distinguishing between a model's general inability to choose methods vs. a specific domain's difficulty).

Additionally, the definition of success relies on the relative gap metric $g$. The paper sets a hard threshold ($g > 0.1$) for "Surpass-SOTA" but does not discuss the sensitivity of this threshold. If the SOTA baseline has measurement noise or if the metric is sensitive to hyperparameters, the binary classification of success/failure could be unstable. A sensitivity analysis varying the threshold is required. Finally, the cost analysis relies on estimated token counts for several models. Without error bounds on these estimates, the conclusion that "insufficient compute budget" is a primary failure mode (24.4%) is statistically weak, as the cost data itself is imprecise. The authors must re-run the statistical analysis to include confidence intervals, address the hierarchical data structure, and quantify uncertainty in derived metrics.
