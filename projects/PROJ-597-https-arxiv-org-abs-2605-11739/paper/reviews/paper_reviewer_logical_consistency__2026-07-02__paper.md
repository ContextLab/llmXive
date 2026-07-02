---
action_items:
- id: 1b4a848cd4f4
  severity: writing
  text: 'Nomenclature and Claim Inconsistency: The abstract and introduction introduce
    the proposed method as EffOPD with a 3x acceleration claim. However, the text
    also frequently references AlphaOPD (and AlphaRL in the related work) with a 2x
    acceleration claim. In the Introduction, the text states, "we propose EffOPD...
    achieves an average training acceleration of 3x," but later in the same section
    (and in the abstract body), it mentions "AlphaOPD... achieves up to 2x." It is
    unclear if EffOPD is a re'
- id: e6676fb4a4de
  severity: writing
  text: 'Figure Referencing Errors: The logical flow of Section 3.2 is disrupted by
    incorrect figure references. The text refers to "Figure 4 (b)" when discussing
    the "Bottom-k% Subspace" analysis, but the provided figure list includes fig4_2.pdf,
    and the caption for Figure 4 in the text refers to "Subspace evolution and weight
    scaling." The mismatch between the text''s reference to "Figure 4 (b)" and the
    actual content of the figures (which seem to be split or mislabeled in the source)
    makes it impossibl'
- id: fa1e3b8657a6
  severity: writing
  text: 'Scope of Theoretical Justification: The theoretical analysis in Appendix
    A.5 relies on a local linearization of the OPD objective around the base model
    to explain the "Early Low-Rank Lock-in" phenomenon. The derivation shows that
    under a local quadratic approximation, the update direction is determined by the
    initial teacher-student residual. However, the paper claims this "lock-in" persists
    throughout the entire training process (up to 100% progress) and across massive
    model scales. The logical'
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:56:07.886344Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logical argument that On-Policy Distillation (OPD) is more efficient than Reinforcement Learning (RL) due to two properties: "Functional Redundancy Avoidance" and "Early Low-Rank Lock-in." The core logic—that OPD identifies stable update directions early and concentrates updates on high-utility modules—is generally well-supported by the empirical data presented in the figures and tables. The proposed method, EffOPD, logically follows from the observation that early update directions are stable and can be extrapolated.

However, there are significant logical inconsistencies in the manuscript's presentation that undermine the clarity of the central claims:

1.  **Nomenclature and Claim Inconsistency:** The abstract and introduction introduce the proposed method as **EffOPD** with a **3x** acceleration claim. However, the text also frequently references **AlphaOPD** (and **AlphaRL** in the related work) with a **2x** acceleration claim. In the Introduction, the text states, "we propose EffOPD... achieves an average training acceleration of 3x," but later in the same section (and in the abstract body), it mentions "AlphaOPD... achieves up to 2x." It is unclear if EffOPD is a renaming of AlphaOPD, a distinct method, or if the authors are conflating their own results with a cited work. This creates a logical ambiguity regarding the primary contribution and the magnitude of the claimed improvement.

2.  **Figure Referencing Errors:** The logical flow of Section 3.2 is disrupted by incorrect figure references. The text refers to "Figure 4 (b)" when discussing the "Bottom-k% Subspace" analysis, but the provided figure list includes `fig4_2.pdf`, and the caption for Figure 4 in the text refers to "Subspace evolution and weight scaling." The mismatch between the text's reference to "Figure 4 (b)" and the actual content of the figures (which seem to be split or mislabeled in the source) makes it impossible to verify the logical connection between the "Bottom-k% Subspace" argument and the visual evidence provided.

3.  **Scope of Theoretical Justification:** The theoretical analysis in Appendix A.5 relies on a **local linearization** of the OPD objective around the base model to explain the "Early Low-Rank Lock-in" phenomenon. The derivation shows that under a local quadratic approximation, the update direction is determined by the initial teacher-student residual. However, the paper claims this "lock-in" persists throughout the entire training process (up to 100% progress) and across massive model scales. The logical gap between a local approximation (valid only for small $\Delta \theta$) and the global behavior of a non-convex optimization problem over thousands of steps is not bridged. The authors assert that the local mechanism explains the global phenomenon without providing bounds or arguments for why the linearization remains valid as the model diverges significantly from the base.

These issues require revision to ensure the logical consistency between the claims, the evidence, and the theoretical justification.
