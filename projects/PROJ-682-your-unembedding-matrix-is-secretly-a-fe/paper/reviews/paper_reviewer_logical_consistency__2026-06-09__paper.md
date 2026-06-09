---
action_items:
- id: 9d7916207499
  severity: science
  text: The mathematical proof in Appendix sec:proof incorrectly claims V_tau * V_tau^T
    is the identity matrix. For dimensionality reduction (k < d), this is a projection
    matrix, not identity. This invalidates the claim that the transformation preserves
    the original norm.
- id: 7714047b00d5
  severity: science
  text: Table 5 shows filtering the Dominant subspace (Config 3) degrades performance
    (47.53 vs 50.07 baseline), contradicting the claim that both edges of the spectrum
    encode noise. Explain why filtering both edges (EmbFilter) helps while filtering
    Dominant alone hurts.
- id: b24b79ae4b0b
  severity: writing
  text: Clarify the "distance-preserving" claim in Section 4.2. The transformation
    preserves distances within the subspace, not the original Euclidean distance.
    The current phrasing implies original distance preservation, which is mathematically
    false for reduced dimensions.
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:15:14.276693Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: full_revision
---

The paper presents a compelling method for improving LLM text embeddings, but there are significant logical inconsistencies in the mathematical justification and the interpretation of ablation studies that undermine the proposed mechanism.

**1. Mathematical Proof Error (Appendix, sec:proof):**
The proof for Equation 1 claims that $\|\mathbf{z} \bm{\Phi}_\tau^\top\|_2 = \|\mathbf{z}\|_2$ because "$\mathbf{V}_\tau \mathbf{V}_\tau^\top$ is identity". This is mathematically incorrect. $\mathbf{V}_\tau$ is a $d \times k$ matrix (where $k < d$ for dimensionality reduction). $\mathbf{V}_\tau \mathbf{V}_\tau^\top$ is a rank-$k$ projection matrix, not the identity matrix $\mathbf{I}_d$. Consequently, the norm is not preserved ($\|\mathbf{z} \mathbf{P}\|_2 \le \|\mathbf{z}\|_2$). While the equality between the projected form and the reduced coordinate form (Eq 1) is correct, the justification provided is false. This requires correction to maintain logical rigor.

**2. Ablation Contradiction (Table 5, Section 5.3):**
The core hypothesis is that the "edge spectrum" (both largest and smallest singular values) encodes frequent, uninformative tokens. Filtering these should improve performance. However, Table 5 shows that filtering the Dominant subspace (largest singular values, Config 3) results in a score of 47.53, which is *lower* than the Baseline (50.07). Conversely, filtering the Secondary subspace (smallest values, Config 4) improves performance to 53.19.
If both edges encode noise as claimed, filtering either should help, or at least filtering the Dominant edge should not degrade performance. The fact that EmbFilter (filtering both) scores 54.57 (better than Config 4 alone) suggests a complex interaction, but the paper does not explain why the Dominant edge is harmful in isolation yet beneficial in combination. This inconsistency challenges the mechanistic claim that *both* edges are responsible for the representation collapse.

**3. Dimensionality Reduction Claim (Section 4.2):**
The text states the transformation is "distance-preserving." Based on the math error above, this is imprecise. It preserves distances *relative to the subspace projection*, not the original space. Since the downstream tasks rely on cosine similarity or dot products, the claim should be clarified to avoid implying that original distances are maintained, which they are not.

These issues require revision to ensure the mechanism and mathematical claims are logically sound.
