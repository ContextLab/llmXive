---
action_items:
- id: 858e8e18e26d
  severity: writing
  text: The paper presents a compelling hypothesis regarding the "knowledge boundary"
    in agentic visual generation and proposes a co-training framework to discover
    it. However, the evidentiary support for the central claims relies on experimental
    designs that do not fully rule out alternative explanations such as random variance,
    baseline asymmetry, or confounding model scale. First, the primary results in
    Table 1 (Section 4.2) and the progression in Figure 3 are reported as single-point
    estimates (e.g.
artifact_hash: acdadb0a7d8b66991ef14c7c4247fe346cb02f508281ed63c55a7e05db3f0d02
artifact_path: projects/PROJ-1067-search-beyond-what-can-be-taught-evolvin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-16T02:55:20.547435Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling hypothesis regarding the "knowledge boundary" in agentic visual generation and proposes a co-training framework to discover it. However, the evidentiary support for the central claims relies on experimental designs that do not fully rule out alternative explanations such as random variance, baseline asymmetry, or confounding model scale.

First, the primary results in Table 1 (Section 4.2) and the progression in Figure 3 are reported as single-point estimates (e.g., "31.8" for Klein-4B Phase 2) with no indication of variance. In generative modeling, performance can fluctuate significantly across different random seeds due to the stochastic nature of diffusion sampling and DPO preference pair construction. A gain of 2.6 points (Phase 1 to Phase 2) is reported as a definitive improvement, but without standard deviations or confidence intervals from multiple seeds (e.g., 3-5 runs), it is impossible to determine if this effect is robust or merely a lucky initialization. The claim that the method produces "monotonic improvement" is currently unsupported by statistical evidence of stability.

Second, the comparison of the proposed method against baselines suffers from asymmetry in model capability and tuning. The "ReasonedSearch" baseline (Section 3.3) utilizes a frontier VLM (Gemini-3-Flash) for the gating decision, whereas the proposed method uses a fine-tuned 8B model. The "Oracle" baseline in Table 1 also uses this frontier model. The paper claims the 8B co-trained model "matches or exceeds" the Oracle, but this comparison conflates the benefit of the co-training protocol with the inherent superiority of the frontier model's reasoning capabilities. A fair test of the *protocol* requires comparing the co-trained 8B model against a non-co-trained 8B model (or a similarly scaled baseline) to isolate the effect of the RFT calibration. Currently, the design cannot distinguish whether the gains come from the "teach-then-search" mechanism or simply from using a stronger reasoner than the naive baselines.

Finally, the "BlindSearch" baseline is defined as searching for every gap, while the proposed method learns to abstain. However, the "ReasonedSearch" baseline (which also abstains) is implemented with a much stronger model than the proposed method's reasoner. The paper does not provide a control where the *same* 8B reasoner is used for both the baseline (SFT only) and the proposed method (SFT + RFT) to isolate the specific contribution of the rejection-sampling finetuning. Without this ablation, the claim that the *calibration* is the key driver of the "selectivity" (recovering NoSearch performance) remains plausible but not rigorously established.

To strengthen the evidence, the authors should report results with seed variance, ensure baselines use comparable model scales and tuning efforts, and include an ablation isolating the RFT phase from the SFT warm-up.
