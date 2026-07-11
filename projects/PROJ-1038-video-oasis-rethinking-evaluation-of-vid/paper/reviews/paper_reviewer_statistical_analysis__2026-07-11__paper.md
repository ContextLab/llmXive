---
action_items:
- id: ea989c80f777
  severity: writing
  text: The statistical treatment in this paper is generally descriptive, which is
    common for benchmark auditing papers, but it lacks necessary rigor in quantifying
    uncertainty and validating baselines. First, the paper relies heavily on aggregate
    accuracy percentages (e.g., "55% of samples," "92.7% shortcut ratio," "35.6% accuracy")
    presented as precise point estimates in Tables 2, 3, 4, 5, 6, 7, 8, 9, and 10.
    There is no reporting of standard deviation (SD), standard error (SE), or confidence
    interval
artifact_hash: f0c16b304e278e372ae68ce72c73490fb948c6f63a71aa660ad21d1de4b7a1fb
artifact_path: projects/PROJ-1038-video-oasis-rethinking-evaluation-of-vid/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:07:12.102875Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment in this paper is generally descriptive, which is common for benchmark auditing papers, but it lacks necessary rigor in quantifying uncertainty and validating baselines.

First, the paper relies heavily on aggregate accuracy percentages (e.g., "55% of samples," "92.7% shortcut ratio," "35.6% accuracy") presented as precise point estimates in Tables 2, 3, 4, 5, 6, 7, 8, 9, and 10. There is no reporting of standard deviation (SD), standard error (SE), or confidence intervals (CI) for these aggregates. Since these numbers are derived from aggregating results across 14 different benchmarks and multiple models, the variance across these sources is unknown. A reader cannot determine if a reported "92.7%" is a stable finding or an artifact of a specific subset of benchmarks. The authors should report the standard deviation across the 14 benchmarks for the aggregate metrics to demonstrate the robustness of the "shortcut prevalence" claim.

Second, the "random-chance baseline" of 25.6% cited in Section 4.2 and used to interpret model performance as "marginally above random" is not explicitly derived. This number implies an average of approximately 3.9 options per question (1/0.256). However, the paper does not provide the distribution of multiple-choice options (e.g., how many questions have 3, 4, or 5 choices) across the 14 audited benchmarks. If the option distribution is skewed, the true random baseline could differ significantly. The authors must explicitly state the option distribution or calculate the weighted random baseline based on the actual dataset composition to ensure the "random chance" comparison is valid.

Third, in Section 5.1 (Table 8), the paper claims that temporal grounding yields "consistent improvements" (e.g., Eagle2.5: 31.5% → 32.9%). These are presented as single point estimates without any statistical test. Since the same test set is used for both the baseline and the ablation, the difference should be evaluated using a paired statistical test (such as McNemar's test for classification accuracy or a paired bootstrap) to determine if the improvement is statistically significant or within the noise of the evaluation. Reporting a p-value or a confidence interval for the difference is necessary to support the claim of improvement.

Finally, while the paper uses an ensemble of models for categorization (Section 4.1), it does not report the inter-annotator agreement (e.g., Cohen's Kappa) for the 122 manually inspected samples or the consensus rate for the LLM ensemble. Given the reliance on these categories for the final evaluation split, a measure of annotation reliability is missing.
