---
action_items:
- id: 2b443c738d5a
  severity: science
  text: Correct the mathematical proof in the Appendix claiming the projection matrix
    is identity.
- id: 0da91ea9b31f
  severity: writing
  text: Soften claims of "universal pattern" in Abstract and Introduction to reflect
    limited model scope.
- id: e4989ccf4acf
  severity: writing
  text: Rephrase "actively writing" in Abstract to avoid implying unproven causal
    mechanisms.
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:18:15.298728Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several strong claims that exceed the evidence provided, necessitating a minor revision.

First, the theoretical justification for dimensionality reduction in Section 4.2 and the Appendix contains a significant mathematical error. The proof (Appendix, "Equivalence Transformation Proof") asserts that $\mV_\tau \mV_\tau^\top$ acts as the identity matrix, implying $\|\vz \Phi^\top\|_2 = \|\vz\|_2$. However, for $\tau > 1$, this is a projection operator onto a lower-dimensional subspace, not the identity. Consequently, the claim that the transformation is "distance-preserving" (Section 4.2) is technically incorrect regarding Euclidean norms in the original space. While the method preserves relative similarity within the subspace, overstating this as a general distance-preserving transformation misrepresents the mathematical properties of the proposed linear map.

Second, the paper claims a "universal pattern inherent to LLMs" (Introduction, Line 102) and that the phenomenon is "observed across different language model families" (Abstract, Line 49). This broad generalization is drawn from experiments on only three models (Qwen, Llama, Mistral) with specific parameter sizes. While the findings are consistent across these three, characterizing this as a universal law across all LLM architectures is an overreach given the limited scope.

Third, the Abstract (Line 43) states the subspace is "actively writing these frequent tokens," implying a specific causal mechanism within the model's generation process. The evidence provided (Logit Spectroscopy) demonstrates a strong correlation between spectral components and token logits but does not definitively prove the unembedding matrix actively generates these tokens as the sole driver.

Please correct the mathematical proof in the Appendix to accurately reflect the projection nature of the transformation. Additionally, revise the Abstract and Introduction to use more conservative language regarding universality and causality, ensuring claims are strictly bounded by the experimental scope and correlational evidence.
