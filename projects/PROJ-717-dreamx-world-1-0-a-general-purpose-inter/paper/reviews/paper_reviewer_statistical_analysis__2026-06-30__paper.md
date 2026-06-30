---
action_items:
- id: a96738a544d3
  severity: science
  text: Table 1 and Table 2 report single-point performance metrics (e.g., 73.75,
    84.76) without confidence intervals, standard errors, or p-values. Given the use
    of VLM-based evaluators (Gemini-3.1-Pro) and human studies, variance is expected.
    Statistical significance of the claimed improvements over baselines (HY-WorldPlay,
    LingBot-World) is not established. Re-run evaluations with multiple seeds or bootstrap
    resampling to provide uncertainty estimates.
- id: d80ebd2e8a4a
  severity: science
  text: The 'Gain-based Scoring' methodology in Section 5.3 (Memory Evaluation) subtracts
    baseline scores from revisit scores but does not report the statistical distribution
    of these gains. Without reporting the variance of the baseline and revisit metrics,
    it is impossible to determine if the observed gains (e.g., +3.92 in PSNR) are
    statistically significant or within the noise floor of the metric. Include t-tests
    or non-parametric equivalents with effect sizes.
- id: 0b1079cfced1
  severity: science
  text: The Human Preference Study (Section 5.4) reports raw percentages (e.g., 57.5%
    win rate) but lacks statistical testing (e.g., binomial test or chi-squared) to
    confirm these preferences are significant against the null hypothesis of random
    choice (50%). Additionally, the sample size (number of human evaluators and trials)
    is not explicitly stated, preventing power analysis or reproducibility of the
    study.
- id: d87a44b71fac
  severity: science
  text: The artifact detection metric relies on a VLM (Gemini-3.1-Pro) evaluating
    frames at 2 FPS. The paper does not report the inter-rater reliability (e.g.,
    Cohen's Kappa) if multiple VLM passes were averaged, nor does it quantify the
    variance of the VLM's judgment. Treating VLM outputs as deterministic ground truth
    without error bars is statistically unsound for a primary evaluation metric.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T05:19:37.668905Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the evaluation section is insufficient to support the paper's quantitative claims. While the evaluation suite is comprehensive in scope, the analysis lacks the necessary statistical depth to distinguish genuine model improvements from random variance or evaluator noise.

First, all quantitative results in Tables 1, 2, and 3 are presented as single-point estimates. There are no confidence intervals, standard deviations, or standard errors reported for any metric, including the camera control scores, visual quality metrics, or memory consistency gains. In generative modeling, where results can vary significantly based on random seeds, prompt sampling, or stochastic VLM behavior, reporting only the mean is misleading. The authors must re-run the evaluation pipeline with multiple random seeds (e.g., $N \ge 5$) and report the mean $\pm$ standard deviation.

Second, the claim that DreamX-World "outperforms" baselines is not statistically validated. For instance, in Table 1, the overall score difference between DreamX (84.76) and HY-WorldPlay (80.79) is 3.97 points. Without a hypothesis test (e.g., paired t-test or Wilcoxon signed-rank test) and a reported p-value, it is unclear if this difference is statistically significant or merely a result of sampling variance. The same applies to the memory consistency gains in Table 3; the "gain" metric is a difference of means, but the variance of that difference is unreported.

Third, the Human Preference Study (Section 5.4) is critically under-reported. The paper states win/tie/loss rates (e.g., 57.5/14.4/28.1) but fails to specify the total number of comparisons ($N$) or the number of human annotators. Without $N$, it is impossible to calculate the margin of error or perform a binomial test to verify if the win rate significantly exceeds the 50% chance baseline. The current presentation treats the observed percentages as absolute truths rather than estimates with uncertainty.

Finally, the reliance on VLMs (Gemini-3.1-Pro) for artifact detection and quality scoring introduces a new source of variance that is not quantified. The paper mentions averaging two passes per test case but does not report the agreement rate between these passes or the stability of the VLM's scoring across different prompts. This lack of reliability analysis undermines the objectivity of the "Artifact" and "Quality" metrics.

To proceed, the authors must provide a full statistical analysis including: (1) error bars (95% CI) for all table metrics, (2) p-values for pairwise comparisons against baselines, (3) explicit sample sizes and statistical tests for the human study, and (4) an analysis of VLM scorer variance/reliability.
