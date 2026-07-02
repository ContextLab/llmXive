---
action_items:
- id: e284199b5727
  severity: fatal
  text: The proof in Appendix~\ref{sec:proof} contains a fatal algebraic error. The
    authors claim V_tau * V_tau^T is the identity matrix, which is false for a truncated
    projection matrix (it is a projection, not identity). Consequently, the claim
    that ||z * Phi^T||_2 = ||z||_2 is incorrect; the transformation reduces the norm.
    The dimensionality reduction claim relies on this flawed identity.
- id: 7e566566e27e
  severity: science
  text: The ablation study in Table~\ref{tab:ablation} lacks statistical significance
    testing. With 49 datasets, reporting single-point averages without standard deviations,
    confidence intervals, or paired t-tests makes it impossible to determine if the
    observed gains (e.g., +9.0%) are robust or due to random variance.
- id: 3297b95092f1
  severity: science
  text: The reverse-engineering of the "average" token in Section~\ref{sec:interpret}
    uses log(frequency) as a proxy for logits without accounting for the temperature
    scaling or the bias term (vb) omitted in Equation 5. This approximation may introduce
    systematic bias in the identification of the edge spectrum subspace.
artifact_hash: 23484ba7b10cc08665875915717095ae222ff4767aae24d46926097ffc583ae4
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:56:15.975051Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis and mathematical derivations supporting the core claims of the paper require significant revision.

First, the proof of the distance-preserving property in Appendix~\ref{sec:proof} (lines 1080-1095) is mathematically incorrect. The authors state that "considering that V_tau * V_tau^T is identity," which is false. Since V_tau consists of a subset of columns from an orthogonal matrix V, V_tau * V_tau^T is a projection matrix onto a subspace, not the identity matrix. Consequently, the equality ||z * Phi^T||_2 = ||z||_2 does not hold; the norm is strictly reduced unless z lies entirely within the subspace. This invalidates the claim that the transformation is distance-preserving in the Euclidean sense, which is central to the dimensionality reduction argument in Section 4.2.

Second, the experimental results in Table~\ref{tab:main_results} and Table~\ref{tab:ablation} lack necessary statistical rigor. The paper reports mean performance across 49 datasets but provides no measure of variance (e.g., standard deviation) or statistical significance testing (e.g., paired t-tests or bootstrap confidence intervals). Given the magnitude of the reported improvements (up to 14.1%), it is essential to demonstrate that these gains are statistically significant and not artifacts of the specific dataset split or random initialization. Without this, the robustness of the method across different tasks cannot be verified.

Finally, the derivation of the "average" token in Section 3.2.2 relies on the approximation log(frequency) ≈ logit. This ignores the softmax normalization constant and the bias term vb, which the authors admit to omitting. While the bias might be constant, the normalization term varies with the vocabulary distribution. A more rigorous statistical justification or sensitivity analysis regarding this approximation is needed to ensure the identified "edge spectrum" is not an artifact of the simplified logit estimation.
