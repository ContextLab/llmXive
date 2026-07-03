---
action_items:
- id: 30a49141b9f1
  severity: science
  text: The claim that Lens achieves 19.3% of Z-Image's compute cost (Abstract, Intro)
    compares 192K A100 hours to 314K H800 hours. This conflates hardware generations
    (A100 vs H800) and does not normalize for FLOPS or memory bandwidth. The paper
    cites raw TFLOPS (312 vs 989.5) but fails to provide a unified compute metric
    (e.g., total FLOPs or normalized GPU-hours) to substantiate the '19.3%' figure.
    Re-calculate efficiency using a hardware-agnostic metric.
- id: eb46ee29b699
  severity: science
  text: The GenEval score of 0.930 (Table 1) is exceptionally high compared to prior
    SOTA (e.g., LongCat-Image 0.870). The paper does not report standard deviation,
    confidence intervals, or the number of seeds used for evaluation. Given the sensitivity
    of GenEval to prompt rewriting (Section 4, 'Prompt for GenEval Benchmark'), the
    lack of statistical variance reporting makes it impossible to assess if the improvement
    is robust or an artifact of specific prompt engineering.
- id: d13d5e8249f5
  severity: science
  text: The ablation study on RL dataset diversity (Table 2) shows GenEval scores
    of 0.916 (1/4 set) vs 0.930 (Full set). The absolute gain is small (1.4%), yet
    the text claims 'full diversity is critical.' The paper lacks a statistical significance
    test (e.g., t-test) to determine if this difference is meaningful or within the
    noise of the evaluation metric, especially given the small sample size of the
    RL set (8K prompts).
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:31:05.721671Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling efficiency narrative, but the scientific evidence supporting the central claims of "training efficiency" and "SOTA performance" requires stronger statistical grounding and hardware normalization.

First, the primary claim of achieving "19.3% of the training compute" (Abstract, Section 1) relies on a direct comparison of 192K A100 GPU hours against 314K H800 GPU hours. This comparison is methodologically flawed as it ignores the architectural differences between A100 and H800 GPUs. While the authors provide raw TFLOPS figures (312 vs 989.5), they do not integrate these into a unified compute metric (e.g., total FLOPs or normalized GPU-hours). Without normalizing for the specific hardware capabilities, the 19.3% figure is an apples-to-oranges comparison that overstates the efficiency gain. The evidence for this claim is currently insufficient to support the magnitude of the assertion.

Second, the benchmark results, particularly the GenEval score of 0.930 (Table 1), lack necessary statistical rigor. The paper reports single-point estimates without standard deviations, confidence intervals, or the number of random seeds used for evaluation. In generative modeling, performance can vary significantly based on sampling seeds and prompt variations. The absence of variance metrics makes it impossible to determine if the reported improvements over competitors (e.g., LongCat-Image at 0.870) are statistically significant or within the margin of error. Furthermore, the heavy reliance on prompt rewriting (Section 4) introduces a confounding variable; without reporting the variance across different prompt rewriting seeds or strategies, the robustness of the 0.930 score is questionable.

Finally, the ablation study on RL dataset diversity (Table 2) presents a marginal improvement (0.916 to 0.930) as a critical finding. The text asserts that "full diversity is critical" based on this ~1.4% absolute gain. However, without a statistical significance test (e.g., a t-test) or error bars, it is unclear if this difference is distinguishable from noise. Given the relatively small size of the RL dataset (8K prompts), the statistical power to detect such small effects is low. The authors should provide statistical validation to support the claim that the full dataset is strictly necessary versus a smaller subset.

In summary, while the engineering contributions appear sound, the scientific evidence regarding efficiency claims and performance robustness needs to be strengthened with normalized compute metrics and rigorous statistical reporting.
