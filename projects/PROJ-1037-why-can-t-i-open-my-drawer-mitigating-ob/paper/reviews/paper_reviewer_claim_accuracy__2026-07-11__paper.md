---
action_items:
- id: bc7b854b162f
  severity: writing
  text: Section 3.2 cites Fig 3 for a cosine similarity of 0.92, but Fig 3 shows FSP/FCP
    curves. The value is in supplementary Fig S1. Update the citation to the correct
    figure or move the analysis to the main text.
- id: ec7d989e1a1e
  severity: writing
  text: Section 5.2 claims Jung et al. has the lowest unseen accuracy among CLIP baselines,
    but Table 1 shows AIM (39.19%) is lower than Jung (53.55%). Qualify the claim
    to 'lowest among compositional baselines' or correct the comparison set.
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:11:33.248825Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a coherent diagnosis of object-driven shortcuts in ZS-CAR and proposes a method to mitigate them. The diagnostic metrics are well-defined and the experimental setup is rigorous. However, there are two specific instances where the text makes claims that do not align with the cited evidence or tables.

First, in Section 3.2, the authors state that the baseline C2C yields a cosine similarity of 0.92 between forward and reversed verb features, citing Figure 3. However, Figure 3 (fig_diagnosis_baseline) displays learning curves for FSP/FCP and accuracy, not cosine similarity. The 0.92 value is actually presented in the supplementary Figure S1 (fig_cosine_sim). This is a citation mismatch that should be corrected to point to the correct figure.

Second, in Section 5.2, the text claims that "Jung et al. yields the lowest unseen composition accuracy among the CLIP baselines" on Sth-com. According to Table 1 (sth_com.tex), the AIM baseline achieves 39.19% unseen accuracy, while Jung et al. achieves 53.55%. Since AIM is lower, the claim is factually incorrect as stated. The authors should clarify that Jung et al. has the lowest accuracy among the *compositional* baselines (excluding simple adapter baselines like AIM) or correct the statement to reflect the actual data.

These are minor issues that can be resolved with text edits and do not affect the core validity of the proposed method or the main experimental conclusions.
