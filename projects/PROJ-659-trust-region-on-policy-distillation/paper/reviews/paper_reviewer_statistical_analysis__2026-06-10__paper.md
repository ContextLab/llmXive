---
action_items:
- id: 9d40e75b6275
  severity: science
  text: Report training variance across multiple random seeds (N>=3) for all main
    results. Current '32 times evaluation' refers to inference sampling, not training
    stability, undermining claims of consistent improvement.
- id: 60e37e7a1a16
  severity: science
  text: Include standard deviations or 95% confidence intervals in Tables t1, tab:opd_results,
    and main. Point estimates alone do not support statistical significance of reported
    gains (e.g., +3.06 points).
- id: e32f434ff565
  severity: science
  text: Justify the fixed learning rate (5e-6) and step count (200) for all baselines.
    Uniform hyperparameters may introduce optimization bias against methods requiring
    different tuning schedules.
artifact_hash: 74f03d7ab60f5026cfa7c71878897ef40634611691a4c76f5e68e8e21f3101c9
artifact_path: projects/PROJ-659-trust-region-on-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T10:47:57.127523Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling empirical evaluation, but the statistical analysis supporting the core claims lacks rigor required for publication.

First, the evaluation protocol described in "Benchmark Evaluation" (lines 430-435) states results are "the average accuracy of 32 times evaluation." This phrasing typically denotes inference sampling (e.g., majority voting over 32 generations) rather than independent training runs. However, the "Main Results" section claims "consistent improvements" (e.g., +3.06 points over OPD) based on single-point estimates in Tables `tab:opd_results` and `main`. Without variance reported across multiple training seeds (N $\ge$ 3), it is statistically impossible to distinguish genuine methodological improvements from random initialization variance. The claim of "stable reasoning optimization" (Abstract) is unsupported without training-level error bars.

Second, significance testing is absent. Tables `t1`, `tab:opd_results`, and `main` report only mean accuracy. For benchmark tasks like AIME (30 problems), the binomial variance is non-negligible. Confidence intervals or p-values from paired tests (e.g., Wilcoxon signed-rank across problems) are necessary to validate whether TrOPD's gains over REOPOLD are statistically significant or noise.

Third, the "Benchmark Training" section (lines 440-445) fixes the learning rate at $5 \times 10^{-6}$ and steps at 200 for all methods. While this controls variables, it risks unfair comparison if baselines converge at different rates. A sensitivity analysis or justification for this uniformity is needed to ensure the observed performance gap is not an artifact of suboptimal baseline hyperparameters.

Finally, clarify the aggregation method for the "32 times evaluation." Is accuracy computed via majority vote or any-correct? This affects the effective sample size and variance calculation. Please revise the statistical reporting to include training variance, confidence intervals, and hyperparameter sensitivity analysis to substantiate the reported gains.
