---
action_items:
- id: 7d8cad50e682
  severity: writing
  text: The manuscript relies heavily on specialized terminology that creates a barrier
    for non-specialist readers, particularly in the abstract and introduction. The
    term "principals" is used repeatedly to refer to users or stakeholders without
    a clear definition, which is a significant jargon hurdle. Similarly, "memory governance"
    is introduced as a core concept but is not explicitly distinguished from standard
    "memory management" or "access control" until later in the text, leaving the reader
    to infe
artifact_hash: 4f01dcbb1424147633a4eb29c69325a37730d0263065af71df4aeeea6414618e
artifact_path: projects/PROJ-767-gatemem-benchmarking-memory-governance-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T16:17:39.451469Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that creates a barrier for non-specialist readers, particularly in the abstract and introduction. The term "principals" is used repeatedly to refer to users or stakeholders without a clear definition, which is a significant jargon hurdle. Similarly, "memory governance" is introduced as a core concept but is not explicitly distinguished from standard "memory management" or "access control" until later in the text, leaving the reader to infer its specific meaning.

The phrase "hidden checkpoints" is used frequently but is essentially a technical term for "unannounced test queries"; a brief parenthetical explanation would improve clarity. "Leak-target annotations" is another instance of internal jargon that should be replaced with "annotations of sensitive data to be protected." The concept of "active forgetting" is central to the paper but is not defined in plain language; it should be explicitly described as the ability to permanently delete and not recover information upon request.

In Section 3, terms like "normalized action," "judge specification," and "episodic forgetting" are used without sufficient context for a general audience. "Normalized action" could be simplified to "standardized response category," and "judge specification" should be clarified as the "evaluation criteria." The term "over-refusal rate" is a compound jargon term that could be simplified to "rate of unnecessary refusals."

Section 4 introduces "backbone" models, which is common ML jargon but should be defined as "base model" or "underlying language model" for clarity. The term "governance-complete" is awkward and undefined; "fully compliant with governance requirements" is clearer. "Soft-overreach" is a specific attack vector term that needs a plain-language explanation, such as "subtle attempts to bypass access controls."

Appendix A1 uses "current-state anchors" and "delete-to-attack gap," which are metaphorical and technical terms, respectively. These should be replaced with "recent updates that define the current state" and "the time elapsed between a deletion request and a recovery attempt." Finally, "field-level agreement" in Appendix A4 should be simplified to "agreement on individual metric fields." Addressing these instances of jargon will make the paper more accessible to a broader audience without sacrificing technical precision.
