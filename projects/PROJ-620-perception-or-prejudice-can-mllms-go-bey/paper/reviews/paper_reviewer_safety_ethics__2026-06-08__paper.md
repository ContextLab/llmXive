---
action_items:
- id: cef8ce5ea2d2
  severity: writing
  text: Explicitly state IRB/ethics committee approval status for the 24 human annotators
    involved in Stage 1 and Stage 5 of the pipeline (Appendix \ref{app:human}).
- id: bb7d57584347
  severity: writing
  text: Clarify the consent scope of the source ChaLearn V2 data regarding personality
    inference and ensure the new annotation layer does not exceed original consent
    terms.
- id: 0697d5f6500d
  severity: writing
  text: Strengthen the limitation statement in Appendix \ref{app:ethics} to explicitly
    prohibit using the benchmark for high-stakes decision-making (e.g., hiring) without
    regulatory approval.
artifact_hash: 37d4da743146174451c6b81c250d33af63eaf988a8502062dfca5a6325ae068a
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T10:47:30.626906Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This manuscript addresses a critical safety and ethics dimension by introducing a benchmark (MM-OCEAN) that evaluates whether MLLMs ground personality judgments in evidence rather than superficial cues. The inclusion of an Ethics and Responsible Use section (Appendix \ref{app:ethics}) and a Datasheets for Datasets disclosure (Appendix \ref{app:datasheet}) is commendable and aligns with NeurIPS standards. The authors correctly identify the high-risk nature of personality inference in hiring and surveillance contexts, citing the EU AI Act and discouraging downstream deployment without consent.

However, there are three specific gaps requiring revision to ensure full ethical compliance:

1. **Human Annotation Ethics:** Appendix \ref{app:human} describes a Stage 1 and Stage 5 human annotation process involving 24 trained annotators who verified cues and drew bounding boxes. While compensation is mentioned ("local research-assistant hourly rate"), there is no explicit statement regarding IRB or institutional ethics committee approval for this human-subject work. Even if annotators are employees, ethical oversight for data labeling involving human subjects (the video subjects) or annotator welfare should be documented. Please add a sentence confirming IRB approval or exemption status for the annotation phase.

2. **Source Data Consent:** The benchmark draws videos from ChaLearn First Impressions V2 (Section 3.3). While the dataset is public, the original consent scope for crowd-sourced personality scores may not cover the new, fine-grained behavioral grounding analysis introduced here. The Ethics section should explicitly confirm that the new annotation layer does not violate the original data license or consent terms, or clarify if the original subjects consented to personality analysis specifically.

3. **Misuse Mitigation:** The current language in Appendix \ref{app:ethics} ("We discourage downstream use...") is appropriate for research but could be stronger given the high-risk nature of the task. Consider adding a specific prohibition clause in the dataset license or README (referenced in the paper) that explicitly forbids using MM-OCEAN for automated hiring, insurance, or law enforcement profiling without explicit regulatory clearance.

Addressing these points will solidify the paper's ethical standing and ensure responsible dissemination of a capability that is inherently dual-use.
