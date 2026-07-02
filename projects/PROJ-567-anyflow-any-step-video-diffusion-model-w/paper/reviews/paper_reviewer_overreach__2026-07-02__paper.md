---
action_items:
- id: 6998ded086a2
  severity: writing
  text: The manuscript makes several strong claims regarding the novelty and performance
    of AnyFlow that require tighter alignment with the presented evidence to avoid
    overreach. First, the assertion in the Abstract and Introduction that AnyFlow
    is the "first any-step video diffusion distillation framework based on flow maps"
    is a significant claim. While the authors correctly cite the concurrent work TMD
    (Nie et al., 2026) in Section 2, which also utilizes a flow map formulation for
    bidirectional video
artifact_hash: 3aad81d8a133042c5a798b8bf30d90974b62e8f4dc5a0e7e17e6ccdaa711ef9d
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:26:37.462058Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several strong claims regarding the novelty and performance of AnyFlow that require tighter alignment with the presented evidence to avoid overreach.

First, the assertion in the Abstract and Introduction that AnyFlow is the "first any-step video diffusion distillation framework based on flow maps" is a significant claim. While the authors correctly cite the concurrent work TMD (Nie et al., 2026) in Section 2, which also utilizes a flow map formulation for bidirectional video diffusion, the "first" qualifier remains absolute. The distinction made (TMD uses architectural sharing vs. AnyFlow's trajectory decomposition) is valid, but the phrasing should be nuanced to acknowledge TMD's concurrent contribution to the "flow map" category, perhaps by specifying "first to support causal architectures via flow map backward simulation" or similar, to prevent the claim from being technically inaccurate regarding the broader class of flow map distillation.

Second, the performance comparisons in the Abstract and Introduction (e.g., AnyFlow 84.05 vs. Krea-Realtime 83.25) present a potential over-interpretation of the data. The text explicitly states that baseline scores for Krea and others are "taken directly from the original papers," while AnyFlow is re-evaluated. While the authors claim the protocol is identical, differences in prompt sets, random seeds, or evaluation infrastructure between the original Krea paper and this re-evaluation could introduce variance. Claiming a definitive "surpassing" without explicitly confirming that the baseline was re-run under the *exact* same seed and prompt conditions (or acknowledging the limitation of cross-paper comparison) overstates the statistical certainty of the improvement.

Finally, the claim that the model "continues to improve as the number of sampling steps increases" (Abstract, Section 1) is supported by data points at 4 and 32 NFEs. However, the paper does not provide a monotonicity analysis or intermediate steps (e.g., 8, 16 NFEs) to prove a consistent upward trend. It is possible that performance plateaus or fluctuates between these points. Extrapolating a continuous "improvement" trend from two discrete points is a minor overreach. The authors should either include intermediate NFE results to substantiate the trend or rephrase the claim to indicate that performance is "maintained or improved at higher step budgets" to remain strictly within the bounds of the provided data.
