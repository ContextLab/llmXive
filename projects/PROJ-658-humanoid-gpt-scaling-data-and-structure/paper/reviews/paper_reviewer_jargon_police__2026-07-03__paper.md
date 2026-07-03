---
action_items:
- id: dac9ce71411e
  severity: writing
  text: The manuscript relies heavily on domain-specific acronyms and jargon that
    are not defined at their first occurrence, creating unnecessary barriers for non-specialist
    readers. In the Abstract and Section 1, the term "G1-retargeted" and the standalone
    "G1" are used without defining the Unitree-G1 humanoid robot. Similarly, "MoCap"
    is used repeatedly (e.g., Section 1, Section 3.1) without spelling out "motion
    capture." Section 3.1 introduces "PD controller" and "DoF" (degrees of freedom)
    without de
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:29:23.009433Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and jargon that are not defined at their first occurrence, creating unnecessary barriers for non-specialist readers. 

In the **Abstract** and **Section 1**, the term "G1-retargeted" and the standalone "G1" are used without defining the Unitree-G1 humanoid robot. Similarly, "MoCap" is used repeatedly (e.g., Section 1, Section 3.1) without spelling out "motion capture." 

**Section 3.1** introduces "PD controller" and "DoF" (degrees of freedom) without definition. While standard in control theory, a general audience requires these expanded. The text also uses "priv." as a superscript for state ($s_t^{priv.}$) without explicitly stating "privileged" in the immediate context, relying on the reader to infer the meaning of "privileged observations."

In **Section 3.2**, "DAgger" is introduced as a framework without defining the acronym (Dataset Aggregation). The loss function "SmoothL1Loss" is named but not described. 

**Section 2** and **Table 1** use "MoE" (Mixture of Experts) without definition. 

The **Appendix** (sec/X_suppl.tex) contains "t-SNE" without expansion and a likely typo "video-esti" which should be "video-estimated." Finally, the **Conclusion** mentions "VLA-style" without defining Vision-Language-Action models.

These instances of undefined jargon and acronyms violate the principle of accessibility for a broader scientific audience. The authors should ensure every acronym is defined at first use and replace shorthand terms with their full names where appropriate.
