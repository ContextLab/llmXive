---
action_items:
- id: 28e6c585b677
  severity: writing
  text: The manuscript relies heavily on specialized terminology that, while standard
    in specific agent-memory sub-fields, creates barriers for a broader audience.
    The most significant issue is the use of undefined acronyms and statistical jargon.
    In Appendix A.1, the term "arm" is used repeatedly to describe the experimental
    conditions (e.g., "anonymous arm label," "memory condition are hidden"). This
    is standard clinical trial terminology but is opaque to general readers; "condition"
    or "variant" woul
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:27:15.776006Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that, while standard in specific agent-memory sub-fields, creates barriers for a broader audience. The most significant issue is the use of undefined acronyms and statistical jargon. In Appendix A.1, the term "arm" is used repeatedly to describe the experimental conditions (e.g., "anonymous arm label," "memory condition are hidden"). This is standard clinical trial terminology but is opaque to general readers; "condition" or "variant" would be more accessible. Similarly, the acronym "W-L-T-NA" appears in Section 5.2 and Appendix A.3 without ever being defined as "Win-Loss-Tie-Not-Available," forcing the reader to guess the meaning or search for it.

In Section 3.1, the term "round-0" is introduced to denote the initial generation stage. While the context implies it is the first turn, the specific notation "round-0" (as opposed to "initial generation" or "turn 0") is a piece of internal jargon that should be explicitly defined upon first mention to ensure clarity for readers not steeped in multi-turn agent protocols.

Furthermore, the paper frequently uses metaphorical jargon to describe technical mechanisms. Phrases like "bounded repair surface" (Section 3.2) and "scoped slide-local revision" (Abstract and Section 1) are dense. "Repair surface" is not a standard term in presentation generation and acts as a barrier; replacing it with "the specific set of slides and elements to be edited" would improve readability without losing precision. The term "re-contextualizing" in Section 1 is also vague; "re-reading" or "re-processing" the full deck would be a plainer alternative.

Finally, the distinction between "active temporary memory" and "working memory" is sometimes blurred. While "working memory" is a standard cognitive science term, the paper's specific definition ("session-scoped state layer") should be clearly distinguished from the general concept early on to avoid confusion. The authors should audit the text for similar instances of field-specific shorthand and replace them with plain English equivalents or provide immediate definitions.
