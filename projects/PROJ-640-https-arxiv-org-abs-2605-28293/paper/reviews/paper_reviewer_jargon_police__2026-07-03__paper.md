---
action_items:
- id: 2f7a5c62ef4e
  severity: writing
  text: The manuscript relies heavily on domain-specific acronyms and coined terms
    that are not consistently defined at their first point of use, creating barriers
    for readers outside the immediate niche of reinforcement learning for recommendation
    systems. In the Abstract and Introduction, the metrics IoI and IoR are introduced
    as acronyms without their full names (Increment of Interest, Increment of Rank).
    A general reader cannot understand the contribution without flipping to Section
    2 (Preliminaries
artifact_hash: 59e5ed22cd4a5270f33af7ca1a0149493d75bf5066fd8fe56191e1e437bc5c6a
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:02:04.977658Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and coined terms that are not consistently defined at their first point of use, creating barriers for readers outside the immediate niche of reinforcement learning for recommendation systems.

In the **Abstract** and **Introduction**, the metrics **IoI** and **IoR** are introduced as acronyms without their full names (Increment of Interest, Increment of Rank). A general reader cannot understand the contribution without flipping to Section 2 (Preliminaries) to decode these terms. The Abstract should explicitly state "Increment of Interest (IoI)" and "Increment of Rank (IoR)" to ensure immediate clarity.

Similarly, the term **SmGD** (Smooth-Guided Data) appears in **Appendix e001** (Table 2 and Section "Smooth-Guided Data Construction") without a prior definition in the main text. While the full phrase is used in the section header, the acronym is used in the table and subsequent discussion without a clear "SmGD (Smooth-Guided Data)" introduction, which is a standard requirement for accessibility.

The acronym **PAdv** is used in the caption of **Figure 2** ("...via ... Position-Specific Advantage Estimation (PAdv)") and in the text, but the main body text in Section 3.2 refers to the method as "Position-Specific Advantage Estimation" without explicitly linking the acronym to the full term in the same sentence where the acronym is first used in the narrative flow. The figure caption defines it, but the text should mirror this definition upon first mention to avoid confusion.

Additionally, **RQ-VAE** is mentioned in **Appendix e001** ("RQ-VAE (5 levels...)") without expansion. While "VAE" is common, "RQ" (Residual Quantization) is specific jargon that should be spelled out for a broader audience. Finally, the term **SOTA** is used in the Abstract; while ubiquitous in computer science, it is an acronym that should be written as "state-of-the-art" in the first instance to adhere to plain language principles.

These issues are fixable by simple textual edits (expanding acronyms) and do not require re-running experiments, but they are necessary to make the paper accessible to the intended broad audience.
