---
action_items:
- id: f8d0c4227bbd
  severity: writing
  text: The claim of being the 'first NVFP4 training and inference system for long
    video generation' (Abstract) is potentially overreaching. Qualify with 'to our
    knowledge' or explicitly rule out prior video-specific NVFP4 work in Related Work.
- id: 97eed549beea
  severity: writing
  text: Attributing the 'clean pipeline' solely to 'high-quality infrastructure' (Intro)
    overstates causality. The paper lacks ablation isolating infrastructure from dataset
    or algorithmic design. Temper claims to reflect correlation rather than sole causation.
- id: e60fa0df608e
  severity: writing
  text: Claiming NVFP4 'preserves semantics' (Teaser) without a controlled NVFP4-vs-BF16
    ablation within the same pipeline is overreach. The observed quality may stem
    from the 'clean pipeline' or SP, not just quantization. Clarify this limitation.
artifact_hash: de9cc7b61426b053f14e2745d8dcacce77bcfbd73c84f2c8e9aae072a3bf9bd1
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:01:24.885219Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on potential over-claiming and over-reach in the manuscript.

The paper makes several strong claims regarding the novelty and causal impact of its contributions that appear to slightly exceed the immediate evidence provided.

First, the claim in the Abstract and Conclusion that LongLive-2.0 is the "first NVFP4 training and inference system for long video generation" is a definitive statement of novelty. While the authors cite NVFP4 applications in LLMs, they do not explicitly demonstrate that no prior work has applied NVFP4 to video diffusion or autoregressive video models. Given the rapid pace of the field, this absolute claim risks overreach. It would be more scientifically rigorous to phrase this as "To our knowledge, the first..." or to provide a brief discussion in the Related Work section explicitly ruling out prior video-specific NVFP4 implementations.

Second, the Introduction and Section 1 argue that the "remarkably clean training pipeline" (direct AR fine-tuning without ODE/DMD) is a direct result of the "high-quality infrastructure." This implies a causal relationship where the infrastructure *enables* the algorithmic simplification. However, the paper does not present an ablation study isolating the infrastructure's role from other factors, such as the specific AR objective, the dataset quality, or the base model architecture. It is possible that the clean pipeline is a result of the algorithmic design choices rather than the infrastructure alone. Attributing the algorithmic simplification primarily to the infrastructure without controlling for these variables constitutes an over-interpretation of the results.

Third, the Teaser caption and Section 5.3 claim that NVFP4 "preserves the overall scene composition, subject structure, and shot-level semantics" of the BF16 baseline. While the VBench scores in Table 4 are high, the experimental setup compares the full LongLive-2.0 system (NVFP4 + Balanced SP + Clean Pipeline) against baselines that may use different pipelines. The paper lacks a controlled experiment comparing NVFP4 vs. BF16 *within the exact same training pipeline* to isolate the quantization effect on semantic preservation. Without this control, attributing the preservation of semantics solely to NVFP4 is an overreach, as the "clean pipeline" or other infrastructure components could be the primary drivers of the quality.

These issues are primarily matters of phrasing and the strength of causal claims rather than fundamental flaws in the science. The authors should temper their language to reflect the limitations of their ablation studies and ensure novelty claims are appropriately qualified.
