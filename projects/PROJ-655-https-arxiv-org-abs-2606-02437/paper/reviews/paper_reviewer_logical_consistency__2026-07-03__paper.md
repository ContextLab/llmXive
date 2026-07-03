---
action_items:
- id: 735eb5c00c13
  severity: science
  text: The claim that OLoRA-tail's minor subspace initialization prevents KL explosion
    lacks a derived causal mechanism. The text asserts stability but does not explain
    why the minor subspace specifically satisfies RL trust-region constraints better
    than the principal subspace, beyond empirical observation.
- id: 21a62c0a4da3
  severity: science
  text: The argument that LoRA diversity yields 'complementary policies' rather than
    'stochastic noise' is not fully supported. The paper does not rule out that distinct
    LoRA variants are merely different local optima of the same policy surface, weakening
    the leap to 'collective intelligence'.
- id: f60d1d0dc3a1
  severity: writing
  text: The claim that 'Scale Up without Scale Down yields expensive priors' assumes
    necessity without proof. The paper shows both are possible but does not demonstrate
    that the Scale Up experiment would fail without the specific Scale Down techniques,
    leaving the dependency chain unproven.
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T08:38:49.843435Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent three-axis framework (Scale Up, Down, Out) for PEFT, and the logical flow between these sections is generally sound. The dependency chain (Scale Up enables Scale Down, which enables Scale Out) is clearly articulated. However, several causal claims lack sufficient internal justification or alternative explanations.

First, in Section 3.2.1, the paper claims that OLoRA-tail (initializing from minor singular vectors) prevents KL divergence explosion in RLVR, whereas standard LoRA and OLoRA (principal vectors) fail. The text attributes this to "preserving pretrained geometry" and avoiding "aggressive updates." While the empirical results (Figure 4) are clear, the logical link between "minor singular vectors" and "RL stability" is not rigorously derived. The paper cites a general "KL leash" argument but does not explicitly show why the minor subspace specifically satisfies the trust-region constraints better than the principal subspace in the context of the specific RL objective used. This leaves a gap between the proposed mechanism and the observed outcome.

Second, in Section 5.1, the paper argues that the performance gain from aggregating 198 distinct LoRA models (Collaboration) over repeated sampling (Repetition) proves the existence of "complementary policies" and "collective intelligence." The logic assumes that because the models were trained with different data permutations/masking, they represent distinct strategies. However, the paper does not explicitly rule out the alternative hypothesis that these models are simply converging to different local optima of a similar policy surface, and that the gain is merely due to ensemble diversity rather than true complementary reasoning capabilities. The distinction between "stochastic noise" and "complementary policies" is asserted but not fully logically disentangled.

Finally, the dependency claim in the Introduction ("Scale Up without Scale Down yields expensive priors") is a strong logical assertion. While the paper demonstrates that Scale Up is possible (Kimi K2) and Scale Down is beneficial (OLoRA-tail), it does not provide a logical or empirical argument that the Scale Up experiment *would have failed* without the Scale Down techniques. The necessity of the coupling is assumed rather than proven, which weakens the logical consistency of the "dependency chain" argument.
