---
action_items:
- id: 23939733aaba
  severity: science
  text: Report confidence intervals or standard errors for the main metrics (U, A,
    F, MGS) in Table 1. The current point estimates do not convey the variance across
    the 2,218 checkpoints or the stability of the LLM-as-a-judge evaluation.
- id: 1391906e6e87
  severity: science
  text: Clarify the statistical basis for the 'maximum absolute difference of 1.04
    percentage points' in the judge-human validation (Table A4). Specify if this is
    a mean absolute error, a max deviation, or a bound derived from a specific statistical
    test, and provide the sample size (N) for each metric in the validation set.
- id: 01d58f622809
  severity: science
  text: The multiplicative MGS formula (U * (1-A) * (1-F)) creates a non-linear scale.
    When comparing methods, consider reporting statistical significance (e.g., bootstrap
    confidence intervals or paired tests) for MGS differences, as small changes in
    A or F can disproportionately affect the final score.
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:08:31.977976Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis framework in GateMem is conceptually sound, defining clear metrics for Utility (U), Access Control (A), and Active Forgetting (F). The use of an LLM-as-a-judge is justified by the human validation study in Appendix A4, which reports high agreement (Cohen's κ > 0.93). However, the presentation of results lacks necessary statistical rigor to support the strong comparative claims made in the main text.

First, Table 1 presents point estimates for all metrics across 42 experimental conditions (7 methods × 6 backbones) without any measure of uncertainty. Given that the evaluation involves 2,218 checkpoints, the variance of these estimates should be reported. For instance, a difference of 1.5% in MGS between two methods might be statistically insignificant if the standard error is high. The authors should report 95% confidence intervals (e.g., via bootstrapping over episodes or checkpoints) or standard errors for the primary metrics. This is particularly critical for the "Efficiency Trade-offs" section, where latency and token counts are averaged without variance.

Second, the human validation results in Table A4 state a "maximum absolute difference of 1.04 percentage points" but do not specify the statistical nature of this bound. Is this the maximum observed error across the sample, or a bound derived from a specific confidence level? The table lists N values for field-level agreement (e.g., N=96 for Access leakage), but the aggregate metric comparison lacks the corresponding sample sizes or the method used to aggregate the errors. Without this, the claim of "closely match" is qualitative rather than quantitative.

Finally, the multiplicative nature of the Memory Governance Score (MGS) introduces non-linearity. A method with high utility but slightly higher leakage can have a drastically lower MGS than a method with moderate utility and zero leakage. While the formula is logically defensible, the paper should acknowledge that standard parametric tests (like t-tests) may not be appropriate for comparing MGS directly due to this non-linearity and the bounded nature of the metric [0, 1]. Non-parametric tests or bootstrap-based significance testing would be more appropriate for validating the claim that "Long-Context... achieves the highest MGS."
