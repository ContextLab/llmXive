---
action_items:
- id: 2eb2f36e387d
  severity: writing
  text: Define 'ASR' (Attack Success Rate) and 'TASR' (Targeted ASR) at their first
    occurrence in Section 5.1. Currently, they appear as acronyms without expansion,
    hindering non-specialist readers.
- id: 9d2f10286179
  severity: writing
  text: Replace the term 'epistemic resilience' with a plain-language definition or
    synonym (e.g., 'resistance to misinformation') upon first introduction in Section
    1. The current definition is abstract and relies on specialized philosophical
    terminology.
- id: ae422a5e5fb7
  severity: writing
  text: Clarify 'Type 1' and 'Type 2' delivery protocols in Section 4.4. While described,
    the labels are arbitrary jargon; consider renaming them to 'Focused Injection'
    and 'Full Bundle Injection' for immediate clarity.
- id: ffc5fb6a5ecf
  severity: writing
  text: Define 'Gwet AC2' in Section 5.7. The statistical metric is used to report
    inter-rater agreement but is not explained, excluding readers unfamiliar with
    this specific coefficient.
- id: 5aeb5e367724
  severity: writing
  text: Replace 'content/provenance decomposition' in Section 2 and Table 1 with 'separating
    the false claim from its source type' to avoid unnecessary technical phrasing.
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:54:04.116498Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology and undefined acronyms that create a barrier for non-specialist readers, particularly those in clinical or general AI safety fields.

First, the core concept of "epistemic resilience" is introduced in Section 1 without a plain-language equivalent. While the authors define it as "preserving correct medical judgment," the term itself is philosophical jargon. A simpler phrase like "resistance to misinformation" or "truthfulness under pressure" would be more accessible.

Second, critical metrics are introduced as acronyms without definition. In Section 5.1, "ASR" and "TASR" appear immediately without being spelled out as "Attack Success Rate" and "Targeted Attack Success Rate." Similarly, "Gwet AC2" is cited in Section 5.7 without explanation. These acronyms are standard in specific sub-fields but obscure the meaning for a broader audience.

Third, the "Type 1" and "Type 2" labels for delivery protocols (Section 4.4) are arbitrary jargon. The text describes them as "Focused" and "All-option," but the labels themselves do not convey meaning. Renaming these to "Focused Injection" and "Full Bundle Injection" would improve readability.

Finally, phrases like "content/provenance decomposition" (Section 2, Table 1) and "answer-grounded" (Section 1) are unnecessarily technical. "Decomposition" could be "separation," and "answer-grounded" could be "based on a specific correct answer." These changes would significantly lower the entry barrier for readers without a background in formal evaluation metrics.
