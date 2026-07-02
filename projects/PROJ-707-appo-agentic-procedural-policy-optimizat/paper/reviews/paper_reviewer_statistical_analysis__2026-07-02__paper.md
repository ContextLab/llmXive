---
action_items:
- id: d086395bdf52
  severity: science
  text: Theorem 1 assumes Var(R|D_i) is monotone in BS_i to prove variance reduction.
    This is a critical unverified assumption. The authors must provide empirical evidence
    (e.g., a scatter plot of BS vs. reward variance across decision points) or a theoretical
    justification for this monotonicity, as it is the linchpin of the variance reduction
    claim.
- id: 935ade484ff1
  severity: science
  text: "Theorem 2 relies on the bound 1-\u03B5' \u2264 A^fut(s) \u2264 1+\u03B5'.\
    \ However, Eq. 7 defines A^fut via a clipped exponential of a sum of log-ratios.\
    \ The clipping is applied to the final value, but the unclipped sum could theoretically\
    \ violate the bound if the discount factor \u03B3 or the number of steps is large.\
    \ The authors should explicitly demonstrate that the clipping parameters (\u03B5\
    ') are sufficient to guarantee the bound holds for all visited states in their\
    \ experiments."
- id: 18462a1e42d0
  severity: science
  text: Table 1 and Table 2 report mean accuracy scores but omit standard deviations
    or confidence intervals. Given the stochastic nature of RL training and the small
    sample sizes of some benchmarks (e.g., AIME24 has only 30 problems), the statistical
    significance of the reported improvements (e.g., +2.45 points) cannot be assessed.
    Please report standard deviations over multiple seeds or perform significance
    tests (e.g., paired t-tests) to validate the gains.
- id: 44b81a170b64
  severity: science
  text: "The ablation study in Table 4 compares APPO against variants (e.g., BS\u2192\
    Ent, w/o A^fut) but does not report p-values or confidence intervals for the differences.\
    \ With multiple comparisons across datasets and backbones, the risk of Type I\
    \ error increases. Please include statistical significance testing for the ablation\
    \ results to confirm that the observed drops are not due to random variance."
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:35:55.292650Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally sound in its experimental design, utilizing multiple benchmarks and ablation studies. However, several critical statistical assumptions and reporting standards require clarification to fully support the theoretical and empirical claims.

First, the theoretical foundation relies heavily on unverified assumptions. Theorem 1 (Variance Reduction) posits that the conditional reward variance is monotone in the Branching Score (BS). This is a strong assumption that is not empirically validated in the text. Without a plot showing the relationship between BS and reward variance across the decision points, the claim that APPO reduces variance compared to random branching remains theoretical and potentially unfounded. Similarly, Theorem 2 (Policy Improvement Bound) assumes the future-aware advantage term is bounded within $[1-\epsilon', 1+\epsilon']$. While the authors apply clipping, they do not demonstrate that the underlying unclipped values (which depend on the sum of log-ratios over a trajectory) would naturally fall within this range or that the clipping does not introduce bias that invalidates the bound.

Second, the reporting of experimental results lacks necessary statistical rigor. Tables 1 and 2 present mean accuracy scores across 13 benchmarks but omit standard deviations, standard errors, or confidence intervals. In reinforcement learning, where results can vary significantly based on random seeds and hyperparameter sensitivity, reporting only the mean is insufficient. This is particularly problematic for benchmarks with small sample sizes, such as AIME24 (30 problems), where a single correct/incorrect trajectory can swing the mean by several percentage points. The authors should report results over multiple independent runs (e.g., 3-5 seeds) with error bars or standard deviations to allow for a proper assessment of the stability and significance of the improvements.

Finally, the ablation studies in Table 4 and the scaling analysis in Table 3 compare different configurations but do not include statistical significance tests. Given the multiple comparisons performed (across datasets, backbones, and components), the risk of false positives is non-negligible. The authors should perform paired t-tests or non-parametric equivalents (e.g., Wilcoxon signed-rank test) to confirm that the performance differences between APPO and its variants are statistically significant. Without these tests, the claim that "all components contribute to the final gains" is not statistically robust.
