---
action_items:
- id: 027a5ba735c5
  severity: writing
  text: The paper presents a large-scale dataset and benchmark with extensive quantitative
    results. However, the statistical treatment of these results lacks necessary rigor
    regarding uncertainty and inference. First, uncertainty reporting is absent. Tables
    1 through 6 (e.g., tab:task1_results, tab:scaling_task2) report performance metrics
    (Connectivity, REM, MAPE) as single point estimates (e.g., "97.9%", "73.7%") to
    one decimal place. In deep learning, where results vary significantly across random
    se
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T00:11:41.835495Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a large-scale dataset and benchmark with extensive quantitative results. However, the statistical treatment of these results lacks necessary rigor regarding uncertainty and inference.

First, **uncertainty reporting is absent**. Tables 1 through 6 (e.g., `tab:task1_results`, `tab:scaling_task2`) report performance metrics (Connectivity, REM, MAPE) as single point estimates (e.g., "97.9%", "73.7%") to one decimal place. In deep learning, where results vary significantly across random seeds, training runs, and evaluation splits, a single number is insufficient to establish reliability. The authors must report the mean and standard deviation (or standard error) across at least 3 independent seeds for all reported metrics. Without this, it is impossible to determine if the reported improvements (e.g., the 0.8pp drop in GPS-only ablation) are statistically significant or merely noise.

Second, **multiple comparisons are unaddressed**. Table 1 (`tab:llm_comparison`) evaluates 6 models across 3 metrics, resulting in 18 pairwise comparisons. The paper highlights "best" and "second best" performers without applying any correction for multiple testing (e.g., Bonferroni, Holm, or Benjamini-Hochberg). With 18 tests, the probability of at least one false positive at α=0.05 is approximately 60%. The authors should either apply a correction to the significance levels or explicitly caveat that the rankings are uncorrected and exploratory.

Third, **claims of "no negative transfer" lack statistical backing**. The assertion that the joint model shows "no negative transfer" (Section 5.2) is based on comparing point estimates of the joint model against task-specific models. Without a formal statistical test (e.g., a paired t-test or bootstrap confidence interval on the difference) or variance estimates, this claim is anecdotal. The observed differences (e.g., 73.7% vs 71.0%) may not be statistically distinguishable from zero given the variance inherent in LLM evaluation.

Finally, **precision exceeds support**. Reporting metrics to one decimal place (e.g., "97.9%") implies a precision that is likely unsupported by the variance across seeds. Once standard deviations are calculated, the authors should round their reported means to a precision consistent with the uncertainty (e.g., if SD is 1.2%, reporting "97.9%" is misleading; "98 ± 1%" is appropriate).

These issues do not invalidate the dataset or the general trend of results, but they prevent the quantitative claims from being rigorously interpreted. The authors should re-run experiments with multiple seeds and update the tables to include uncertainty measures and appropriate statistical caveats.
