---
action_items:
- id: 22cb06b94e7b
  severity: science
  text: In Section 5.2, Eq. 9 projects gradients using right singular vectors V_16.
    The text must explicitly confirm this projects the correct dimension (input vs
    output) to logically enforce the claimed rank-16 bottleneck on the update subspace.
- id: aaf9952b8aed
  severity: science
  text: In Section 6.2, the claim that objective mixing breaks the lock assumes the
    cross-covariance term in Eq. 14 is negligible. The paper lacks evidence that this
    term does not maintain OPD geometry at intermediate mixing ratios, weakening the
    causal claim.
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:31:21.034409Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent logical framework linking the "relaxed off-principal regime" to "subspace locking" and finally to "objective composition" as the controlling factor. The progression from static diagnostics (Section 4) to trajectory analysis (Section 5) and control experiments (Section 6) is logically sound. The conclusion that OPD is distinct from a simple interpolation between SFT and RLVR follows well from the presented evidence of early subspace emergence and robustness to runtime perturbations.

However, there are two specific logical gaps regarding the mathematical implementation of the claims:

1.  **Projection Dimensionality (Section 5.2):** The paper claims that constraining training to a rank-16 subspace preserves OPD performance. Equation 9 defines the projection as $g \leftarrow g V_{16} V_{16}^\top$, where $V_{16}$ are the right singular vectors of the cumulative update $\Delta W$. For a weight matrix $W \in \mathbb{R}^{d_{out} \times d_{in}}$, the right singular vectors correspond to the input dimension ($d_{in}$). The text must explicitly clarify whether the gradient $g$ is being projected on its input or output dimension. If $g$ is projected on the wrong dimension (e.g., projecting rows when $V$ spans columns), the "bottleneck" logic fails. The current text assumes the reader infers the correct matrix multiplication order, which is a logical ambiguity in a technical proof.

2.  **Causal Mechanism of Objective Mixing (Section 6.2):** The paper argues that objective mixing breaks the lock because it changes the gradient source, whereas runtime perturbations do not. The mechanistic explanation (Eq. 13-14) posits that the covariance $\Sigma_\alpha$ is a weighted sum of $\Sigma_{OPD}$ and $\Sigma_{RLVR}$. The logical leap is that this mixture *immediately* shifts the dominant subspace away from the OPD lock. The paper does not address the potential for the cross-covariance term $\Sigma_{cross}$ to maintain the OPD geometry at intermediate mixing ratios (e.g., $\alpha=0.5$). Without evidence that the cross-term is negligible or that the eigenvalues of $\Sigma_{OPD}$ and $\Sigma_{RLVR}$ are sufficiently separated to cause an immediate switch, the claim that the "lock" is broken solely by objective composition is not fully supported by the provided derivation.

These issues require clarification in the text or additional analysis to ensure the causal claims are rigorously supported.
