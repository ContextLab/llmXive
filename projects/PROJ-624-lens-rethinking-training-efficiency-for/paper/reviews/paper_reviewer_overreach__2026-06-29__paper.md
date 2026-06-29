---
action_items:
- id: a7718e89c994
  severity: science
  text: Clarify whether baseline models in Table 1 were evaluated with a reasoner
    module to ensure fair comparison of model performance versus system performance.
- id: d7e917c3b338
  severity: writing
  text: Qualify the training compute efficiency claim (19.3%) to explicitly acknowledge
    dependence on Model FLOPS Utilization (MFU) rather than peak TFLOPS alone.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T04:06:53.347015Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes strong claims regarding training efficiency and performance relative to larger models. While the ablation studies support the internal validity of the proposed methods (dense captions, VAE choice), there are concerns regarding the external comparison and efficiency metrics.

First, the claim that Lens "surpasses" state-of-the-art models (Abstract, Introduction) relies on benchmark comparisons in Table 1. However, the table does not explicitly state whether the baseline models (e.g., Z-Image, Qwen-Image) were evaluated with a reasoner module. Section 1 notes that reasoner-based rewriting is "standard practice" and reports Lens results with and without it (Appendix Table "different reasoners"). If baselines were evaluated without reasoners while Lens results include one, the performance advantage is attributed to the system pipeline rather than the training efficiency of the model itself. This risks overclaiming the model's intrinsic capability.

Second, the training compute efficiency claim ("19.3% of the training compute used by Z-Image") normalizes A100 and H800 GPU hours using peak BF16 TFLOPS. While a footnote acknowledges that "Actual efficiency may differ due to memory bandwidth, MFU, and communication overhead," the main text presents the 19.3% figure as a definitive efficiency gain. Training efficiency is heavily dependent on Model FLOPS Utilization (MFU), which varies by architecture and hardware. Without reporting MFU or wall-clock throughput normalized by hardware capability, this claim extrapolates beyond the provided data.

Finally, the multilingual generalization claim ("enabling multilingual generalization from English-only training data") is supported by the language encoder ablation, but Table 1 shows Lens scoring lower on OneIG (ZH) (0.525) compared to Z-Image (0.535). While the abstract claims "surpassing... in several cases," the multilingual performance is not superior to a likely multilingual-trained competitor, suggesting the generalization is present but not necessarily "surpassing" in that domain.

These issues do not invalidate the core contribution but require clarification to prevent over-interpretation of the results.
