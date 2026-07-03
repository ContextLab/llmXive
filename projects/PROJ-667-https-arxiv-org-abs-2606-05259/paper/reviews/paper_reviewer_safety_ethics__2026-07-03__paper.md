---
action_items:
- id: ac2740ad2f01
  severity: writing
  text: The Impact Statement (Section 6) claims annotators were paid $13/h and gave
    informed consent, but lacks specific IRB approval numbers or the name of the ethics
    review board. For a dataset involving human labor and potential sensitive content,
    explicit IRB/ethics committee approval details are required to verify compliance
    with institutional standards.
- id: 16a7ced8182c
  severity: writing
  text: The paper mentions using YouTube API to collect CC-licensed videos (Section
    3.2) but does not detail the content safety filtering process. Given the scale
    (145K videos), there is a risk of inadvertently including harmful, hateful, or
    non-consensual content. A description of the safety filters (e.g., Microsoft Azure
    Content Safety API usage details) and the protocol for handling flagged content
    is needed.
- id: 0691ff3d7858
  severity: writing
  text: The dataset includes 145K videos across professional domains (Healthcare,
    Engineering). The authors must explicitly state whether any personally identifiable
    information (PII) or private patient data was scrubbed from the video sources,
    especially for the Healthcare subset, to ensure compliance with privacy regulations
    (e.g., HIPAA, GDPR) before public release.
artifact_hash: 442b60f42997ea4620ca51b6cec07f843dd48ca52b119472ba764f9d3b1bfbac
artifact_path: projects/PROJ-667-https-arxiv-org-abs-2606-05259/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:02:51.384496Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses safety and ethics primarily in the "Impact Statement" (Section 6) and the "Video Collection" subsection (Section 3.2). While the authors state that all videos are CC-licensed and annotators were paid $13/hour with informed consent, the review identifies three specific areas requiring clarification to meet standard ethical publication requirements for large-scale dataset papers.

First, regarding human subject research, the Impact Statement mentions "informed consent" but does not cite a specific Institutional Review Board (IRB) or Ethics Committee approval number. For a dataset involving human annotators and potentially human subjects in the video content, explicit reference to the governing ethics body (e.g., "Approved by the IRB of [Institution], Protocol #XXXX") is necessary to validate the consent process and labor conditions.

Second, the data collection pipeline relies on the YouTube API to source 145,000 videos. While the authors mention using "Microsoft Azure AI Content Safety" (referenced in the LaTeX source), the manuscript lacks a description of the specific safety thresholds applied or the manual review process for flagged content. Without this, there is a non-trivial risk that the released corpus could contain hate speech, harassment, or other harmful material, which poses a dual-use risk for training models on toxic data.

Third, the dataset covers sensitive domains including "Healthcare" (18 subjects) and "Medicine." The authors must explicitly confirm that a rigorous de-identification process was applied to remove any Personally Identifiable Information (PII) or Protected Health Information (PHI) from the video sources. Given the potential for re-identification in video data, a statement on compliance with privacy regulations (such as HIPAA or GDPR) is essential before the dataset can be considered safe for public release.

These are primarily writing and disclosure issues that can be resolved by adding specific details to the Impact Statement and Data Collection sections.
