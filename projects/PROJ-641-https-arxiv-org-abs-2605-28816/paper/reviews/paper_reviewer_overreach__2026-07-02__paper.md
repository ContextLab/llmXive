---
action_items:
- id: 5078f7c930bd
  severity: science
  text: The claim of generalizing 'without additional training' (Abstract) is overreaching.
    Appendix details show a simplex pool of size 4 was used during training. The model
    was exposed to 4-agent geometry, just not simultaneously active. Refine to 'zero-shot
    generalization to unseen counts within the trained pool'.
- id: 50217513ac00
  severity: science
  text: The claim that Sparse Hub Attention reduces cost to linear in P (Abstract,
    Sec 3.2) assumes fixed K. Table 4 shows quality improves as K increases. If K
    must scale with P for large populations, linearity fails. Clarify if K is fixed
    or adaptive in the scaling analysis.
- id: 12cc02fc5a96
  severity: writing
  text: The '24 FPS' claim (Abstract) lacks hardware context. Appendix notes 32 GB200s
    were used. This overstates general deployability. Qualify as 'on high-end hardware'
    or provide latency breakdowns per agent count to justify the real-time label broadly.
artifact_hash: 23197b85ae0bafaaddd0cb8ec8c0f5430ac77fd724ba8930f4eb33d7998307b0
artifact_path: projects/PROJ-641-https-arxiv-org-abs-2605-28816/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T23:21:27.026929Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several ambitious claims regarding the scalability and generalization of the proposed Gamma-World model. While the technical contributions are sound, there are instances where the extrapolation from the reported experiments to the stated conclusions appears to overreach the specific evidence provided.

First, the claim of generalizing "from two to four players without additional training" (Abstract, Section 1) is slightly misleading. The Appendix (Section "Additional Implementation Details") reveals that the model was trained with a "simplex pool of size 4" and that during training, "we randomly sample 2 of the 4 vertices." This means the model was explicitly trained on the geometric configuration of a 4-vertex simplex, even if only two agents were active at any given step. The model has "seen" the 4-agent geometry during training. The claim should be more precise, stating that the model generalizes to *unseen agent counts* (e.g., 3 or 4) *within the trained simplex pool* without architectural changes, rather than implying a complete lack of exposure to the 4-agent configuration space.

Second, the efficiency claim that Sparse Hub Attention reduces cross-agent attention cost from "quadratic to linear in the number of agents" (Abstract, Section 3.2) requires careful qualification. The derived complexity is $O(P \cdot nL \cdot (nL + nK))$. This is linear in $P$ only if the number of hub tokens $K$ is held constant. However, the ablation study in Table 4 (Appendix) shows that increasing $K$ from 8 to 128 yields consistent improvements in FVD and FID. If $K$ must scale with $P$ to maintain interaction quality in larger populations, the effective complexity may not remain linear. The paper should clarify whether $K$ is fixed or adaptive in the scaling regime and how this impacts the linearity claim.

Finally, the statement that the model enables "real-time action-responsive generation at 24 FPS" (Abstract) is presented as a definitive capability of the method. The Appendix notes this was achieved on "32 NVIDIA GB200s." While impressive, this hardware specification is critical context. Without it, the claim overstates the general deployability of the system. The text should explicitly qualify this performance as being achieved on specific high-end hardware or provide a latency breakdown per agent count to justify the "real-time" label for broader deployment scenarios.
