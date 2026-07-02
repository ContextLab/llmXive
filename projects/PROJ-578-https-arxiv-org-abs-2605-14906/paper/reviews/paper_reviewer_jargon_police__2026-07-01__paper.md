---
action_items:
- id: 7f26f365e7b3
  severity: writing
  text: 'The paper relies heavily on a dense layer of acronyms and specialized terminology
    that creates a barrier for readers outside the immediate sub-field of long-context
    multimodal evaluation. In the Abstract and Introduction, the five core memory
    abilities are introduced solely as acronyms: IE (Information Extraction), MSR
    (Multi-Session Reasoning), TR (Temporal Reasoning), KU (Knowledge Update), and
    AR (Answer Refusal). While Table 1 lists them, the text repeatedly uses the acronyms
    (e.g., "IE and'
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:05:21.179821Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper relies heavily on a dense layer of acronyms and specialized terminology that creates a barrier for readers outside the immediate sub-field of long-context multimodal evaluation.

In the **Abstract** and **Introduction**, the five core memory abilities are introduced solely as acronyms: **IE** (Information Extraction), **MSR** (Multi-Session Reasoning), **TR** (Temporal Reasoning), **KU** (Knowledge Update), and **AR** (Answer Refusal). While Table 1 lists them, the text repeatedly uses the acronyms (e.g., "IE and KU are strongly correlated") without ever explicitly defining them in the narrative flow. This forces the reader to constantly cross-reference tables or guess the meaning, violating the principle of accessibility.

In **Section 3.2**, the phrase "removes cases solvable from **parametric knowledge**" uses a term that, while standard in LLM research, is opaque to general AI practitioners. A plainer phrase like "internal model knowledge" would suffice. Similarly, **Appendix A.4** uses the linguistic term "**anaphor**" to describe the replacement of entity names with image references; "reference" or "placeholder" is more universally understood.

**Appendix A.1** introduces "**pHash**" without definition. While "perceptual hashing" is the expansion, the acronym should be defined at first use. **Appendix C.1** mentions "**MoE**" (Mixture of Experts) without expansion. Finally, **Section 4.1** and **Appendix B.3** reference "**vLLM**" as if it were a common noun; while it is a popular library, it is an acronym that should be introduced (e.g., "the vLLM inference engine") for clarity.

These issues are fixable by simple text edits but currently exclude non-specialist readers from fully engaging with the benchmark's contributions.
