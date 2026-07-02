---
action_items:
- id: 38939c1be99b
  severity: science
  text: The sensitivity analysis (Appendix app:perturbation) reports single-point
    estimates for success rates under perturbations (e.g., 'Plaintext' on ALFWorld)
    without confidence intervals or standard deviations. Given the stochastic nature
    of LLM agent trajectories, a single run per condition is insufficient to establish
    statistical significance. Please report results averaged over multiple random
    seeds (e.g., 3-5) with standard errors or 95% confidence intervals to validate
    the robustness claims.
- id: 8e873433c985
  severity: science
  text: In the injection coefficient analysis (Appendix app:scale), the optimal alpha
    values are selected based on peak performance on a single run. The paper claims
    a 'stable effective injection range' but does not provide statistical tests (e.g.,
    ANOVA or pairwise t-tests with correction) to confirm that the differences between
    alpha levels (e.g., 0.5 vs 0.6) are statistically significant rather than noise.
    Please include significance testing for the scale-performance curves.
- id: 68ecc1edb30c
  severity: science
  text: 'The skill composition results (Table tab:compose) are based on a small sample
    size (31 episodes total: 13 seen, 18 unseen). The reported improvements (e.g.,
    84.6% vs 61.5%) lack statistical validation. With such small N, the variance is
    high. Please report confidence intervals for these proportions or perform a statistical
    test (e.g., McNemar''s test for paired episodes if applicable, or Fisher''s exact
    test) to support the claim that Component Merging is significantly superior.'
artifact_hash: a8058c08d3783326623ffd4fe82cc98eaea95cd3e37911390d531e390197b756
artifact_path: projects/PROJ-685-latentskill-from-in-context-textual-skil/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T17:39:58.230788Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally descriptive, relying heavily on point estimates (success rates, exact match scores) without accompanying measures of uncertainty. While the magnitude of the reported improvements (e.g., +21.4% on ALFWorld seen split) appears substantial, the lack of statistical rigor in the sensitivity and compositionality analyses weakens the empirical support for the claims of robustness and composability.

Specifically, the sensitivity analysis in Appendix \ref{app:perturbation} presents results from what appears to be a single evaluation run per perturbation type. For stochastic LLM agents, performance can vary significantly between runs due to sampling variance. Reporting single-point estimates without standard deviations, standard errors, or confidence intervals makes it impossible to determine if the observed differences between \method{} and the in-context baseline under perturbations (e.g., the 3.6 point drop for \method{} vs 3.1 for in-context) are statistically significant or merely noise. The authors should re-run these experiments with multiple random seeds (at least 3-5) and report the mean and variance.

Similarly, the analysis of the injection coefficient $\alpha$ (Appendix \ref{app:scale}) identifies optimal values based on peak performance but does not statistically validate the "inverted-U" shape or the stability of the optimal range. Without statistical tests (e.g., repeated measures ANOVA or pairwise comparisons with multiple-comparison correction), the claim that the effective range is "stable" is not fully supported.

Finally, the skill composition results (Table \ref{tab:compose}) are derived from a very small sample of episodes (31 total). While the percentage differences are large, the statistical power is low. The authors should provide confidence intervals for these proportions or apply appropriate statistical tests (e.g., Fisher's exact test) to confirm that the gains from Component Merging are not due to chance. The current presentation treats these percentages as deterministic facts rather than estimates with uncertainty.
