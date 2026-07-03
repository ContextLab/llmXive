---
action_items:
- id: b4935b645797
  severity: science
  text: The paper claims Lens achieves '19.3% of the training compute' of Z-Image
    (Abstract, Intro) based on 192K A100 hours vs. 314K H800 hours. This comparison
    conflates hardware generations (A100 vs. H800) and lacks a normalized FLOPs calculation.
    Please provide a normalized compute estimate (e.g., total FLOPs or H100-equivalent
    hours) to substantiate the efficiency claim.
- id: 6c6de01c1a8a
  severity: science
  text: Benchmark results in Table 1 and Appendix tables report single-point scores
    (e.g., GenEval 0.930) without confidence intervals, standard deviations, or p-values.
    Given the stochastic nature of diffusion sampling and the finite size of benchmarks
    (e.g., 553 prompts for GenEval), statistical significance testing or variance
    reporting is required to validate performance differences against baselines.
- id: 1331cac4a119
  severity: science
  text: The RL ablation in Table 2 (RL Training Set diversity) shows performance gains
    with full data but lacks statistical validation. With only three data points (1/4,
    1/2, Full), the trend is suggestive but not statistically robust. Please report
    variance across multiple seeds or apply a significance test to confirm the improvement
    is not due to random fluctuation.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:31:25.180800Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling narrative for training efficiency in text-to-image models, but the statistical rigor supporting the quantitative claims requires strengthening.

First, the central claim of "19.3% of the training compute" (Abstract, Section 1) relies on a direct comparison of GPU hours between A100 (Lens) and H800 (Z-Image) hardware. This is a methodological flaw in statistical comparison; H800s offer significantly higher FLOPs per hour than A100s. Without normalizing these figures to a common compute unit (e.g., total FLOPs or H100-equivalent hours), the efficiency claim is not statistically sound. The authors must provide a normalized compute metric to validate the magnitude of the efficiency gain.

Second, the benchmark results presented in Table 1 (Main Results) and the Appendix tables (e.g., GenEval, OneIG) report single-point estimates (e.g., 0.930 for GenEval) without any measure of uncertainty. Diffusion model generation is inherently stochastic, and benchmark scores can vary based on random seeds and sampling schedules. The absence of confidence intervals, standard deviations, or results averaged over multiple independent runs makes it impossible to determine if the observed differences between Lens and baselines (e.g., Qwen-Image, Z-Image) are statistically significant or within the margin of error.

Finally, the ablation study on RL dataset diversity (Table 2) presents a monotonic improvement trend (0.916 -> 0.920 -> 0.930) based on only three data points. While the trend is logical, the lack of variance reporting or significance testing (e.g., t-tests) leaves the robustness of this finding unverified. Given the high cost of RL training, confirming that the full dataset provides a statistically significant improvement over the 1/2 subset is crucial.

The authors should re-run key experiments with multiple seeds to report variance, normalize the compute efficiency metrics, and include statistical significance tests for all comparative claims.
