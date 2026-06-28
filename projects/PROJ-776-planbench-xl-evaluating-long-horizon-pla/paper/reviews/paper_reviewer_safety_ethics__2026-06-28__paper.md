---
action_items:
- id: c4f3158ebd10
  severity: writing
  text: Appendix H (Human Annotation) describes five annotators rating tools but lacks
    IRB approval or informed consent documentation. Add a statement confirming ethical
    guidelines followed.
- id: a16b9298cc01
  severity: writing
  text: The dataset release (HuggingFace) requires an explicit statement confirming
    no Personally Identifiable Information (PII) is included, given the 'retail domain'
    context.
- id: 463374be273d
  severity: science
  text: Safety claims rely on models like 'GPT-5.4' which appear non-existent. Clarify
    if these are placeholders; otherwise, safety evaluations are invalid.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:30:44.831431Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript includes a dedicated "Ethics Statements" section (Page 1), which is a positive step. However, several gaps remain regarding human subject protection and data privacy that require clarification before publication.

First, **Human Annotation Ethics**: Appendix H ("Human Annotation") states that "Five annotators" rated tool quality on a Likert scale. While the authors note they are "qualified researchers," there is no mention of Institutional Review Board (IRB) approval or informed consent procedures. Even if the annotators are co-authors, standard ethical guidelines for research involving human participants should be explicitly addressed. Please add a statement confirming that ethical guidelines were followed and whether IRB exemption was obtained.

Second, **Data Privacy**: The benchmark involves "retail tasks" and "backend records" (Section 3.1, Appendix G). While the authors claim data was "sampled and validated," the release of the dataset on HuggingFace requires an explicit confirmation that no Personally Identifiable Information (PII) is present. Retail data can inadvertently contain sensitive user information. A specific statement on PII scrubbing or synthetic data generation is necessary to ensure compliance with privacy standards.

Third, **Model Validity and Safety Claims**: The paper evaluates models such as "GPT-5.4" and "Gemini-3.5-Flash" (Abstract, Section 4). These model versions appear to be non-existent or future-dated (e.g., bibliography cites 2026). If these models do not exist, the safety and robustness claims derived from their evaluation are scientifically invalid. This impacts the ethical integrity of the safety analysis. Please clarify the model identities or acknowledge this limitation.

Finally, **Dual-Use Considerations**: The "blocking mechanism" (Appendix I) simulates adversarial tool failures. While intended for robustness testing, the authors should briefly discuss potential misuse, such as using the benchmark to train agents to bypass safety filters. A sentence in the "Limitations" or "Ethics" section addressing this would strengthen the safety posture.

Addressing these points will ensure the paper meets community standards for ethical research and data release.
