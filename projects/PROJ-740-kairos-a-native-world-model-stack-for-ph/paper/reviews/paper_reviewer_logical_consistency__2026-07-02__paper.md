---
action_items:
- id: d3ba3d0cb4f7
  severity: writing
  text: 'The logical consistency of the paper is generally strong in its theoretical
    framing but contains gaps in the causal linkage between the proposed mechanisms
    and the empirical claims. First, the theoretical argument for the necessity of
    persistent states (Theorem 1, Section 3.3 and Section 6.1) is logically sound:
    it correctly identifies that if a target depends on history outside a window,
    a window-restricted predictor incurs irreducible excess risk. However, the paper
    asserts that baseline model'
artifact_hash: 926e7dfe86ab0c8e4b8d20a90a842eec681ad7b82ae76075a7b3082533c6260d
artifact_path: projects/PROJ-740-kairos-a-native-world-model-stack-for-ph/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T18:01:16.674024Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is generally strong in its theoretical framing but contains gaps in the causal linkage between the proposed mechanisms and the empirical claims.

First, the theoretical argument for the necessity of persistent states (Theorem 1, Section 3.3 and Section 6.1) is logically sound: it correctly identifies that if a target depends on history outside a window, a window-restricted predictor incurs irreducible excess risk. However, the paper asserts that baseline models (Cosmos, Wan) fail on long-horizon tasks *because* of this theoretical limitation. This causal claim is not fully supported. The paper does not present an ablation study where the window size of a baseline is varied to demonstrate the predicted excess risk, nor does it show that the specific failure modes (e.g., object permanence loss) correlate with the theoretical conditions derived. The connection between the abstract theorem and the specific empirical failures of competitors is asserted rather than demonstrated.

Second, the claim of "mathematically guaranteeing state propagation" (Abstract) rests on the contractive property of the Gated Linear Attention (GLA) module (Theorem 2). The theorem states that if the global memory update is contractive ($\rho < 1$), the error is bounded. While the architecture is designed to be contractive, the paper does not provide empirical verification that the trained model actually satisfies $\rho < 1$ across the training trajectory. Without this verification, the "guarantee" is conditional on an unverified parameter state, weakening the logical force of the claim.

Third, the claim of "linear scaling" in inference time (Abstract, Figure 1c) is supported by latency tables showing linear growth with resolution/frames. However, the paper attributes this primarily to the Hybrid Linear Attention mechanism. This causal attribution is confounded by other efficiency techniques mentioned, such as 4-step distillation, FP8 quantization, and operator fusion. The paper does not isolate the contribution of the attention mechanism to the scaling behavior. It is logically possible that the scaling is linear due to the distillation (reducing steps) or hardware optimizations, while the attention mechanism's complexity reduction is secondary. The current presentation implies the attention mechanism is the primary driver without sufficient evidence to rule out the other factors.

Finally, the definition of "Native" in the title and abstract implies a unified, end-to-end approach. The logical consistency of this claim is slightly undermined by the modular description of the training pipeline (Phase I, II, III) which appears to be a sequential curriculum rather than a truly simultaneous, native joint optimization of all components from the start. While the "Joint World-Action Training" (Stage III) addresses this, the distinction between "curriculum" and "native" is not rigorously defined, leading to a slight ambiguity in the core contribution's definition.
