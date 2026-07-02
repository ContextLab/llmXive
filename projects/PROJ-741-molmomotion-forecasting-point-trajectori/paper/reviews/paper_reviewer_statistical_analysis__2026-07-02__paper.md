---
action_items:
- id: bba691082c71
  severity: science
  text: Report confidence intervals or standard deviations for all quantitative metrics
    in Table 1 (motion prediction) and Table 2 (video generation). The current presentation
    of single-point estimates (e.g., ADE=0.109) lacks statistical context regarding
    variance across the 742 benchmark clips, making it difficult to assess the robustness
    of the reported improvements over baselines.
- id: c1ac1bd0771b
  severity: science
  text: Clarify the statistical methodology for the 'best-of-5' evaluation mentioned
    in Sec 4.1. Specify whether the final metric is the mean of the best-of-5 samples
    or the best-of-5 mean, and provide the variance across these selection events
    to ensure the reported gains are not artifacts of selection bias.
- id: 2e2c0ddd3841
  severity: science
  text: In the robotics transfer section (Sec 4.2), the success rates (e.g., 76.3%
    vs 56.0%) are presented without error bars or significance testing. Given the
    stochastic nature of robot policies and the finite number of evaluation episodes,
    a statistical test (e.g., bootstrap confidence intervals or a t-test) is required
    to substantiate the claim of 'substantial improvement'.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T05:12:54.563216Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in the paper is generally sound in its choice of metrics (ADE, FDE, PWT) and evaluation protocols (best-of-5, held-out benchmarks). However, the reporting of results lacks necessary statistical rigor regarding uncertainty quantification.

In Section 4.1 (Table 1), the authors report single-point estimates for ADE, FDE, and PWT across three datasets (HOT3D, WorldTrack, DAVIS). While the improvements over baselines appear significant in magnitude, the absence of confidence intervals, standard deviations, or standard errors makes it impossible to determine if these differences are statistically significant or merely due to variance in the specific test set composition. For a benchmark of 742 clips, reporting the mean and standard deviation of the error metrics across clips is standard practice.

Furthermore, the "best-of-5" evaluation strategy described in Section 4.1 introduces a selection bias that must be accounted for. The text states, "We follow the point-track forecasting metrics... using best-of-5 evaluation." It is unclear if the reported ADE/FDE values are the average error of the best sample, or if the metric is computed on the single best sample. If the latter, the variance of the selection process should be reported. Without this, the comparison against baselines (which may or may not use the same selection strategy) is potentially confounded.

In Section 4.2, the robotics transfer results (Fig. 4a) show success rates over training steps. The curves are presented without error bands (e.g., 95% confidence intervals over multiple seeds or episodes). Given the high variance often observed in robot learning experiments, the claim that the model "substantially improves" performance requires statistical validation (e.g., a t-test or non-parametric equivalent) to rule out random fluctuation, especially at the 10K step mark where the gap is 51% vs 19%.

Finally, the video generation metrics in Table 2 (VBench scores) are reported to three decimal places (e.g., 0.968). This level of precision implies a high degree of certainty that is likely unsupported by the sample size or the inherent noise in perceptual metrics. Reporting these with appropriate significant figures or confidence intervals would be more scientifically honest.

The paper would benefit from a revised results section that includes measures of dispersion (std dev, CI) for all primary quantitative claims and explicit statistical testing for the key comparative results.
