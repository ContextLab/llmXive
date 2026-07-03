---
action_items:
- id: d81b181f6852
  severity: science
  text: Report uncertainty metrics (e.g., standard deviation or 95% confidence intervals)
    for all benchmark scores in Tables 1, 2, and 3. The current presentation of single-point
    averages (e.g., 63.8, 85.2) obscures the variance across the 650 R-Bench prompts
    or 200 policy rollouts, making it impossible to assess statistical significance
    of the reported gains.
- id: 78386244879a
  severity: science
  text: Clarify the statistical test used to validate the improvements in Table 4
    (RoboTwin) and Table 5 (WorldArena). Specifically, state whether the reported
    success rate differences (e.g., +4.6% average) are statistically significant (p
    < 0.05) given the sample size (200 rollouts/task) and the observed variance in
    the baseline performance.
- id: fe2121b10d7c
  severity: science
  text: In Section 3.1 (Eq. 3), the adaptive threshold for the physics mask is defined
    as the mean score. Justify this choice statistically or provide an ablation on
    the sensitivity of the final results to this threshold (e.g., using median or
    top-k percentile) to ensure the region selection is robust and not an artifact
    of the specific thresholding method.
artifact_hash: f7837dcf8c3e7c1ec478c2e03991867e7e8522c41ddb6acd3b54df07bfe08122
artifact_path: projects/PROJ-803-physisforcing-physics-reinforced-world-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:55:47.467270Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in the paper is generally sound in its design but lacks necessary rigor in reporting uncertainty and significance testing, which is critical for claims of "consistent improvements" across multiple benchmarks.

**1. Lack of Uncertainty Quantification:**
The primary results in Table 1 (R-Bench), Table 2 (PAI-Bench), and Table 3 (EZS-Bench) report single-point average scores (e.g., PF-Cosmos: 63.8, 85.2, 81.1). Given that R-Bench evaluates 650 prompts and the policy experiments involve 200 rollouts per task, the variance across these samples is non-trivial. The absence of standard deviations, standard errors, or 95% confidence intervals makes it impossible to determine if the observed gains (e.g., +9.2% over base) are statistically significant or within the noise of the evaluation metric. For instance, in Table 4 (RoboTwin), the task `shake_bottle` shows a decrease of 3.0% and `stack_bowls_two` a decrease of 6.5%. Without variance estimates, we cannot assess if the average gain of +4.6% is robust or driven by a few outliers.

**2. Missing Significance Testing:**
The paper claims "consistent gains" and "surpassing strong baselines" but does not report the results of any statistical hypothesis tests (e.g., paired t-tests, Wilcoxon signed-rank tests) comparing PhysisForcing against the baselines. In the policy learning section (Sec 4.2), where the sample size is explicitly stated (200 rollouts), a formal test of significance is required to support the claim that the improvement is real and not due to random chance. The current presentation treats the benchmark scores as deterministic values rather than estimates of a distribution.

**3. Sensitivity of Region Extraction:**
In Section 3.1, the physics-informative mask is generated using an adaptive threshold based on the *mean* score of the physics-informative metric (Eq. 3). The choice of the mean is arbitrary; if the distribution of motion scores is skewed (e.g., a few very fast-moving objects), the mean may not represent the "typical" interaction region well. The paper should either provide a justification for using the mean or include a sensitivity analysis showing that the final performance is robust to different thresholding strategies (e.g., median, top-k percentile).

**Recommendation:**
The authors should re-run the evaluation to compute and report standard deviations for all benchmark scores. Additionally, they should perform statistical significance tests for the key comparisons (PhysisForcing vs. Baseline) and report p-values. Finally, a brief sensitivity analysis on the mask thresholding method would strengthen the methodological rigor.
