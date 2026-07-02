---
action_items:
- id: e69d5fa24c15
  severity: writing
  text: The manuscript relies heavily on terminology specific to machine learning
    and computational linguistics, which may alienate the intended audience of literary
    scholars and digital humanists. While the concepts are sound, the presentation
    frequently assumes a background in deep learning that is not universal among the
    paper's potential readers. Specific instances of jargon overuse include the introduction
    of "predictive comparison" (Section 1, line 14) and "stylometric distance" (Section
    2.3, line
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:25:49.366099Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on terminology specific to machine learning and computational linguistics, which may alienate the intended audience of literary scholars and digital humanists. While the concepts are sound, the presentation frequently assumes a background in deep learning that is not universal among the paper's potential readers.

Specific instances of jargon overuse include the introduction of "predictive comparison" (Section 1, line 14) and "stylometric distance" (Section 2.3, line 235) without immediate, plain-English definitions. These terms are central to the paper's contribution but are presented as technical primitives rather than explained concepts. Similarly, "ablation studies" (Section 2.3, line 135) is a standard ML term that should be replaced with "controlled experiments" or "tests removing specific features" to ensure clarity.

The text also uses "token budget" (Section 2.1, line 68), "causal language modeling objective" (Section 2.2, line 92), and "parameter-efficient fine-tuning" (Section 4.3, line 338) without simplification. These phrases act as barriers to entry. For instance, "causal language modeling" is effectively just "predicting the next word," and "parameter-efficient fine-tuning" refers to "updating only a small part of the model."

Finally, the term "open-set attribution problems" (Section 4.1, line 315) is used without context. A brief explanation, such as "situations where the model must identify an author not seen during training," would make the limitation more accessible. The authors should review the text to ensure that every technical term is either defined in simple language or replaced with a more common equivalent, particularly in the Introduction and Methods sections.
