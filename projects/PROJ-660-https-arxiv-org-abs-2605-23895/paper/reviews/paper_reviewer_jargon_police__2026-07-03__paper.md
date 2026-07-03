---
action_items:
- id: 7866b08c87b2
  severity: writing
  text: Define 'fMRI' at first use in the Abstract and Introduction. While standard
    in neuroscience, it is jargon to general readers.
- id: 4235f264265a
  severity: writing
  text: Replace the acronym 'NSD' with 'Natural Scenes Dataset' at first mention in
    Section 4 (Results) and define it clearly.
- id: 27cc0a016a07
  severity: writing
  text: Replace the acronym 'VLM' with 'vision-language model' at first use in Section
    3.1 and Section 4.1 to aid non-specialist readers.
- id: 8d8d4107159f
  severity: writing
  text: Replace the acronym 'ROI' with 'region of interest' in Table 1 and Section
    4.2, or ensure it is defined earlier in the text.
- id: c11733f79723
  severity: writing
  text: Replace the acronym 'TPR' and 'FPR' with 'true positive rate' and 'false positive
    rate' in Section 4.1, or define them immediately upon use.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:27:57.550468Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript makes a strong case for causal validation in visual neuroscience but relies heavily on specialized jargon and unexplained acronyms that may exclude non-specialist readers.

In the Abstract and Introduction, the term "fMRI" is used without definition. While common in the field, a broader audience requires the full term "functional magnetic resonance imaging" at first use. Similarly, in Section 4 (Results), the acronym "NSD" is introduced without spelling out "Natural Scenes Dataset," which is a barrier to entry for readers unfamiliar with this specific dataset.

In Section 3.1 and Section 4.1, the acronym "VLM" is used to refer to "vision-language model." This should be written out fully at the first instance. The same applies to "ROI" (Region of Interest) in Table 1 and Section 4.2, and statistical acronyms "TPR" and "FPR" in Section 4.1, which should be expanded to "true positive rate" and "false positive rate" respectively.

Finally, the phrase "causally validated" is used repeatedly. While precise, it borders on jargon-heavy phrasing. Alternatives like "causally confirmed" or "causally supported" might be slightly more accessible, though the primary issue remains the unexplained acronyms. Addressing these definitions will significantly improve the paper's accessibility without sacrificing scientific rigor.
