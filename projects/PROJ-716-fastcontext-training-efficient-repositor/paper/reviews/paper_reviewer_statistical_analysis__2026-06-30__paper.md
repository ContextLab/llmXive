---
action_items:
- id: 511ede5997d5
  severity: science
  text: Table 1 (tab:e2e_main) reports point estimates for accuracy and token savings
    (e.g., 5.5% gain, 60.3% reduction) without confidence intervals, standard errors,
    or p-values. Given the sample sizes (N=300 for Multilingual, N=200 for Pro), statistical
    significance testing (e.g., McNemar's test for accuracy, bootstrap CIs for token
    reduction) is required to validate the claimed improvements.
- id: f130c0981ebc
  severity: science
  text: The standalone exploration evaluation (Section 4.4, tab:explore_main) presents
    F1 scores but lacks variance metrics. With patch-derived references, the distribution
    of difficulty varies; reporting standard deviations across instances or bootstrapped
    confidence intervals is necessary to assess the robustness of the 73.71 vs 68.57
    F1 difference.
- id: 59047c2b6175
  severity: science
  text: The RL reward function (Eq 1-2, app:reward-details) uses hard thresholds (e.g.,
    n_C < 1 or n_C > 20) without sensitivity analysis. The statistical impact of these
    discrete boundaries on the final policy's performance stability and generalization
    is unquantified. A sensitivity analysis or ablation on reward hyperparameters
    is needed.
artifact_hash: 535aae0d1a0e0d57b4a24f48088ceb2c0ca892fe3b86ecd68f902e6d0b3a9865
artifact_path: projects/PROJ-716-fastcontext-training-efficient-repositor/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T04:10:20.638011Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the evaluation requires significant strengthening before the claims of "up to 5.5% accuracy improvement" and "60% token reduction" can be fully substantiated.

First, **Table 1 (tab:e2e_main)** presents deterministic point estimates for benchmark performance (e.g., GPT-5.4 on SWE-bench Pro rising from 46.0 to 51.5) and efficiency metrics. However, the manuscript omits measures of statistical uncertainty. For the SWE-bench Multilingual benchmark (N=300), the standard error for a proportion near 0.72 is approximately 2.6%. The reported 1.6% to 3.3% gains are within or close to this margin of error. The authors must report **95% confidence intervals** (via bootstrapping or exact binomial methods) and perform **statistical significance testing** (e.g., McNemar's test for paired accuracy comparisons) to demonstrate that the observed improvements are not due to random variance in the test set. Similarly, token reduction claims (e.g., 60.3%) should be accompanied by standard deviations or interquartile ranges to characterize the distribution of savings across instances.

Second, the **Standalone Exploration Evaluation (Section 4.4, tab:explore_main)** reports F1, Precision, and Recall scores (e.g., 73.71 vs 68.57) but provides no variance estimates. Without standard deviations or confidence intervals, it is impossible to determine if the difference between the proposed method and baselines (like RepoSearcher) is statistically significant. Given the heterogeneity of code repositories, a bootstrap analysis over the instance set is required to validate the robustness of these metrics.

Third, the **RL Optimization Details (Appendix A.4)** define reward functions with hard thresholds (e.g., $n_C < 1 \lor n_C > 20$). The statistical sensitivity of the final policy to these specific hyperparameters is not analyzed. A sensitivity analysis varying these thresholds or reporting the distribution of rewards during training would strengthen the reproducibility and validity of the RL approach.

Finally, the **token accounting (Appendix A.5)** aggregates costs across 300 tasks but does not provide a statistical breakdown of the variance in token usage per task type. The claim of "net saving" relies on the assumption that the explorer cost is constant, but the variance in explorer invocation frequency (162 times across 300 tasks) suggests a non-uniform distribution that should be quantified.

In summary, the paper relies on point estimates that lack statistical validation. Re-running the analysis to include confidence intervals and significance tests is necessary to support the central claims.
