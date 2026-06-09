---
action_items:
- id: 3b151a9a66b3
  severity: writing
  text: The proof in Appendix Section 8 incorrectly states that the projection matrix
    V_tau V_tau^T is identity. This is mathematically false when dimensionality reduction
    is applied (V_tau is a subset of columns). While Equation 1 holds, the justification
    misrepresents the transformation as an isometry on the full space. Correct the
    text to accurately describe the projection property.
- id: 94b7f0d9f5cc
  severity: writing
  text: The claim citing lv2024fact states it describes the 'average token' as a 'frequency-weighted
    average embedding over the training corpus'. Verify this attribution explicitly
    matches the cited paper's content to ensure citation accuracy.
- id: 4c3b8fa91e3e
  severity: writing
  text: The term 'Logit Spectroscopy' is attributed to spectral. The cited paper title
    is 'Spectral Filters...'. Clarify if this is a direct quote or a new naming convention
    to ensure proper credit and terminology accuracy.
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:16:57.040119Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

This review focuses on the factual accuracy of claims and citations within the manuscript.

In Section 5 (Methodology Formulation), the authors claim the transformation is "distance-preserving" and provide Equation 1 to support this. However, the proof in Appendix Section 8 (Equivalence Transformation Proof) contains a mathematical inaccuracy. The text states, "considering that $\mV_\tau \, \mV_\tau^{\top}$ is identity," which is incorrect. When $\tau > 1$, $\mV_\tau$ represents a subset of singular vectors, making $\mV_\tau \, \mV_\tau^{\top}$ a projection matrix, not the identity matrix. While the equality in Equation 1 ($\|\vx \Phi^\top - \vy \Phi^\top\| = \|\vx V_\tau - \vy V_\tau\|$) holds, the justification implies the norm is preserved from the original space ($\|\vz\|_2$), which contradicts the dimensionality reduction claim. This misrepresentation should be corrected in the manuscript text to avoid misleading readers about the theoretical guarantees.

Regarding citations, the manuscript attributes the definition of the "average token" as a "frequency-weighted average embedding over the training corpus" to \citet{lv2024fact} (Introduction, Section 1). This is a specific mechanistic claim. Please verify that this paper explicitly defines the average token in this manner to avoid misattribution. Similarly, the term "Logit Spectroscopy" is attributed to \citep{spectral}. The cited work is titled "Spectral Filters, Dark Signals, and Attention Sinks." Ensure the terminology aligns with the source or clarify if this is a novel naming convention introduced by the authors to maintain citation integrity.

The core experimental claims (e.g., 14.1% improvement on MTEB) appear consistent with the provided tables (Table 1). However, the theoretical justifications require textual correction to ensure factual accuracy.
