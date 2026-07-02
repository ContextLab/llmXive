---
action_items:
- id: ea1997105bfc
  severity: science
  text: The claim that Sparse Hub Attention reduces cost to 'linear in agents' (Sec
    3.2) conflates total cost with cross-agent cost. The derived O(P nL^2) term is
    quadratic in sequence length. Clarify that linearity applies only to the cross-agent
    interaction term, not total inference cost.
- id: 062412b2ce13
  severity: science
  text: The 'zero-shot generalization' to 4 players (Sec 4.2) relies on a fixed training
    pool of V=4 (App B). This is inference-time selection from learned identities,
    not true extrapolation to unseen counts (e.g., P=5). Clarify that scaling is bounded
    by the pre-defined pool size V.
artifact_hash: 23197b85ae0bafaaddd0cb8ec8c0f5430ac77fd724ba8930f4eb33d7998307b0
artifact_path: projects/PROJ-641-https-arxiv-org-abs-2605-28816/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:20:18.541351Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical flow of the paper is generally sound, with clear premises leading to the proposed architectural solutions. The motivation for permutation symmetry and the inefficiency of dense attention is well-established. However, there are two specific areas where the conclusions drawn from the premises require tighter logical alignment:

1.  **Complexity Claims (Section 3.2):** The paper asserts that Sparse Hub Attention reduces the cross-agent attention cost from quadratic to linear in the number of agents ($P$). While the derivation in Eq. (10) correctly identifies that the *cross-agent* term scales as $O(P \cdot K)$, the total complexity expression provided, $O(P nL(nL+nK))$, includes a term $P nL^2$ (representing self-attention within each agent's stream). This term is quadratic in the sequence length ($nL$), not linear in $P$ in the way the text implies for the *total* cost. The conclusion that the method is "linear in the number of agents" is only strictly true for the *interaction* component, not the total computational cost. The text should explicitly distinguish between the scaling of the cross-agent communication bottleneck versus the total computational cost to avoid logical overreach.

2.  **Generalization vs. Pool Selection (Section 4.2 & Appendix B):** The paper claims the model "generalizes from two to four players without additional training." The logic here relies on the Simplex Rotary Agent Encoding. However, Appendix B reveals that the training setup uses a fixed simplex pool of size $V=4$, with $P=2$ agents randomly sampled from this pool at each step. Consequently, the model has already "seen" all 4 potential agent identities during training. The ability to run with 4 agents at inference is a result of utilizing the pre-learned vertices from the fixed pool, not a true extrapolation to an unseen number of agents (e.g., $P=5$). The conclusion that the model generalizes "beyond two players" is logically valid only if "generalization" is interpreted as "inference-time flexibility within the trained capacity." If the claim implies the model can handle arbitrary $P > V$ without architectural changes, the evidence does not support it. The text should clarify that the scaling is bounded by the pre-defined pool size $V$.

These issues do not invalidate the core contributions but require precise rephrasing to ensure the conclusions strictly follow the stated premises and experimental setup.
