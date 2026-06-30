---
action_items:
- id: 2fe2f9013824
  severity: science
  text: Report standard deviations or confidence intervals for aggregate metrics (e.g.,
    speedup %) in Table 1. Single-run averages over 100 steps lack statistical significance
    testing for RL stochasticity.
- id: 1092b689de8d
  severity: writing
  text: Specify sample size (N) and 95% CIs for Pearson correlations in Appendix 1.5.
    High r-values without N or error bounds are statistically unstable.
- id: 510f200e4ea4
  severity: science
  text: Add error bars to time-series plots (Figs 5a, App 4) or report step-time variance.
    Single-point baseline comparisons ignore rollout stochasticity and tail effects.
artifact_hash: f5cd2bf8ec4b16de31454f2a2486d371422b77f233615f81a71aa09fed433b62
artifact_path: projects/PROJ-738-efficientrollout-system-aware-self-specu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T10:46:23.977737Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis relies on descriptive statistics without measures of uncertainty, limiting the ability to validate the significance of reported speedups.

**1. Lack of Uncertainty Quantification**
Table 1 and Section 5.1 report mean values for rollout time and speedup over 100 steps but omit standard deviations or confidence intervals. Given the stochastic nature of RL rollouts and the acknowledged "long-tail" dynamics, the variance in these metrics is likely non-negligible. Without error bars or variance metrics, it is impossible to determine if differences (e.g., 12.7% vs 10.8%) are statistically significant. Please report standard deviations for all aggregate metrics and include error bars in time-series figures.

**2. Correlation Analysis Rigor**
Appendix 1.5 reports Pearson correlations ($r \in [-0.99, -0.96]$) between entropy and acceptance but does not state the sample size ($N$). With small $N$, such high correlations can be unstable. The authors must specify the number of data points used for each correlation and provide 95% confidence intervals to demonstrate stability.

**3. Significance of Baseline Comparisons**
The comparison of baselines relies on single-point estimates. To support claims of robust superiority, the authors should perform a statistical test (e.g., paired t-test) comparing step-time distributions across the 100 steps or report results from multiple independent runs with different random seeds.

**4. Handling of Outliers**
The paper notes that a few requests dominate the makespan. Using the arithmetic mean in the presence of heavy-tailed distributions can be misleading. Please clarify if the reported "average" is the mean and consider reporting the median or 90th/99th percentiles to ensure speedup claims are not driven solely by tail behavior.
