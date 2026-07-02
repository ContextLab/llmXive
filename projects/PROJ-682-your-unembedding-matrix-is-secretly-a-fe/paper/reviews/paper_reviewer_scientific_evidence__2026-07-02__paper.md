---
action_items:
- id: 67017525e480
  severity: science
  text: "The proof in Appendix~\ref{sec:proof} claims V_tau * V_tau^T is identity,\
    \ which is false for dimensionality reduction (tau > 1). This invalidates the\
    \ 'distance-preserving' claim. Correct the proof to reflect the projection geometry."
- id: 69383de23335
  severity: science
  text: The 'average' token reverse-engineering assumes the unembedding matrix pseudo-inverse
    recovers a hidden state from log-probs, ignoring bias effects. Provide stronger
    justification or empirical validation for this heuristic across model architectures.
- id: d3459b03854f
  severity: science
  text: The ablation study shows 'Bulk' filtering fails but lacks a theoretical explanation
    for why edge spectra specifically encode high-frequency tokens. Add mechanistic
    analysis to rule out overfitting to specific model spectral properties.
artifact_hash: 23484ba7b10cc08665875915717095ae222ff4767aae24d46926097ffc583ae4
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:55:56.215826Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical evidence that filtering the edge spectrum of the unembedding matrix improves text embedding quality. The use of Logit Lens and Logit Spectroscopy provides a strong mechanistic narrative, and the results across multiple LLM backbones (Qwen, Llama, Mistral) are consistent and robust. The ablation studies effectively demonstrate that the gains are not merely due to dimensionality reduction.

However, the scientific evidence is undermined by a critical mathematical error in the proof of the distance-preserving property (Appendix~\ref{sec:proof}). The authors claim that $\mV_\tau \, \mV_\tau^{\top}$ is the identity matrix, which is only true if $\mV_\tau$ is square. Since the method explicitly reduces dimensions ($\tau > 1$), $\mV_\tau$ is rectangular, and the product is a projection matrix, not the identity. Consequently, the Euclidean distance between vectors is not preserved in the reduced space as claimed. This error invalidates the theoretical justification for the dimensionality reduction claim and must be corrected.

Additionally, the reverse-engineering of the "average" token relies on a heuristic inversion of the unembedding matrix that assumes the bias term is negligible. While the empirical results are convincing, the theoretical robustness of this construction across different model architectures and vocabulary sizes requires stronger justification. Finally, while the ablation studies show that filtering the "bulk" spectrum is detrimental, the paper lacks a deep theoretical explanation for why the edge spectrum specifically encodes high-frequency tokens, leaving the mechanism somewhat empirical. Addressing these points will significantly strengthen the scientific validity of the claims.
