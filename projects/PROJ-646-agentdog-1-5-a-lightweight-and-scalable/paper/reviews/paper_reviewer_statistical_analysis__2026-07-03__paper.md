---
action_items:
- id: daa19dde6095
  severity: science
  text: The statistical rigor of the evaluation section requires significant strengthening
    before the claims can be accepted. First, the central claim of achieving state-of-the-art
    performance with "around 1k samples" (Abstract; Section 4.2) is statistically
    unsupported. The manuscript does not specify the exact number of samples used,
    nor does it provide a variance analysis. Given the high dimensionality of the
    task, a sample size of ~1,000 is small. The authors must report the exact count,
    the standar
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:04:26.707079Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the evaluation section requires significant strengthening before the claims can be accepted.

First, the central claim of achieving state-of-the-art performance with "around 1k samples" (Abstract; Section 4.2) is statistically unsupported. The manuscript does not specify the exact number of samples used, nor does it provide a variance analysis. Given the high dimensionality of the task, a sample size of ~1,000 is small. The authors must report the exact count, the standard deviation of performance across multiple random seeds of the training subset, and ideally, a learning curve or ablation study demonstrating that performance plateaus at this sample size. Without this, the "lightweight" claim is anecdotal.

Second, the reporting of results in Tables 1, 2, and 3 (Sections 4.4.1, 4.4.2, 5.3) relies exclusively on point estimates (Accuracy, F1, ASR) without confidence intervals (CIs) or standard deviations. This is particularly problematic for benchmarks with small test sets, such as CIK-Bench (n=35 trajectories, Table 3, e006). A difference in ASR from 94.29% to 42.86% on 35 samples is a large effect size but requires a formal statistical test (e.g., McNemar's test or Fisher's exact test) to establish significance. Reporting p-values or 95% CIs for all comparative metrics is mandatory to distinguish signal from noise.

Third, the data purification strategy using influence functions (Section 4.2, Eq 1) is presented as a deterministic filter. The authors should provide statistical evidence that the selected subset is indeed "high-value." This could be done by comparing the gradient norms or loss distributions of the selected vs. discarded samples, or by showing that random sampling of the same size yields significantly lower performance. Currently, the selection process is a "black box" with no statistical validation of its efficacy.

Finally, the RL results in Section 5.2 (Table 4, e006) compare SFT, RL, and SFT+RL. The improvements are presented as absolute percentage gains. Given the stochastic nature of RL training, these results should be averaged over multiple seeds with reported standard deviations to ensure the observed gains are reproducible and not due to random initialization variance.
