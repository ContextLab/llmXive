---
action_items:
- id: 5ecca8974cdd
  severity: fatal
  text: The proof in Appendix sec:proof claims V_tau * V_tau^T is the identity matrix,
    which is false for a truncated projection. This invalidates the step ||z * V_tau
    * V_tau^T|| = ||z||. The proof must be corrected to show norm preservation via
    orthogonality of V_tau in the reduced space.
- id: d0d99c10fe38
  severity: science
  text: The derivation of the 'average' token (h_hat = log(p_hat) * W_U^+) ignores
    the non-linearity of Softmax and the log-sum-exp normalization term. The linear
    inversion used is mathematically unsound, making the 'reverse-engineering' claim
    speculative rather than derived.
- id: 7c9ec2234e52
  severity: science
  text: The ablation study shows filtering only the 'Secondary' subspace (Config 4)
    performs nearly as well as the full method, while filtering 'Dominant' (Config
    3) hurts performance. The logic for including the 'Dominant' subspace in the filter
    is not justified by these results.
artifact_hash: 23484ba7b10cc08665875915717095ae222ff4767aae24d46926097ffc583ae4
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:54:05.999436Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the paper is compromised by a critical error in the mathematical proof regarding dimensionality reduction and a gap in the derivation of the "average" token.

First, the proof in Appendix \ref{sec:proof} (lines 1040-1055) contains a fundamental mathematical flaw. The authors state: "considering that $\mV_\tau \, \mV_\tau^{\top}$ is identity, thus we have: $\|\vz \, \mV_\tau \, \mV_\tau^{\top}\|_2 \; = \; \|\vz\|_2$." This is incorrect. $\mV_\tau$ consists of a subset of columns from the orthogonal matrix $\mV$. Therefore, $\mV_\tau \, \mV_\tau^{\top}$ is a projection matrix onto the subspace spanned by those columns, not the identity matrix. The norm $\|\vz \, \mV_\tau \, \mV_\tau^{\top}\|_2$ is generally strictly less than $\|\vz\|_2$ unless $\vz$ lies entirely within that subspace. The claim that the transformation preserves distances *while* reducing dimensionality relies on a false premise in the provided proof.

Second, the derivation of the "average" token in Section 3.2 (lines 630-650) relies on the equation $\hat{\vh} = \log(\hat{\vp}) \, \mW_{\mathcal{U}}^+$. This equation assumes a linear relationship between the log-probabilities of the frequency distribution and the hidden state, derived by inverting the Softmax operation. However, the Softmax function is non-linear, and the relationship $\vq = \operatorname{Softmax}(\vh \, \mW_\mathcal{U}^\top)$ cannot be simply inverted to $\vh = \log(\vq) \, \mW_\mathcal{U}^+$ without accounting for the normalization constant (the log-sum-exp term) which acts as a global bias. While the authors mention omitting the bias term $\vb$ for simplicity, the omission of the normalization term in the log-domain inversion is a significant logical gap that undermines the claim that $\hat{\vh}$ is a precise "reverse-engineered" representation of the average token.

Finally, the ablation study in Table 4 presents a logical tension with the proposed method. The method filters both the "Dominant" (largest singular values) and "Secondary" (smallest) subspaces. However, the ablation shows that filtering only the "Secondary" subspace (Config 4) yields results (Avg 53.19) much closer to the full method (Avg 54.57) than filtering the "Dominant" subspace (Config 3, Avg 47.53) or the "Bulk" (Config 5, Avg 47.13). The paper argues that the "edge spectrum" (both ends) is responsible for the "average" token effect, but the data suggests the "Dominant" edge might not be the primary culprit for the specific degradation being fixed, or that its removal is less critical than the "Secondary" removal. The justification for including the "Dominant" subspace in the filter is not logically derived from the ablation results provided.
