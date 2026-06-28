---
action_items:
- id: 8d873494261b
  severity: writing
  text: Define 'POMDP' at first use in Section 3.1. Spell out 'Partially Observable
    Markov Decision Process' for non-specialist readers.
- id: 4cc98da12203
  severity: writing
  text: Define 'OOD' (Out-of-Domain) in Section 4.1 before using the acronym. Currently
    defined only in Appendix A.1.
- id: 4f38db3dd9f7
  severity: writing
  text: Expand 'KV caching' to 'Key-Value caching' in Section 4.4. This is implementation
    jargon that may confuse readers unfamiliar with Transformer internals.
- id: 5451d2a3a66d
  severity: writing
  text: Simplify or define 'd-separation' and 'collider' in Appendix A.1 proof. These
    are specific probabilistic graphical model terms not standard in all ML subfields.
- id: fdde98ec29d3
  severity: writing
  text: Replace 'action chunk' with 'action sequence' or define it in Section 3.1
    for clarity.
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T06:00:34.283146Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript demonstrates strong technical depth but relies heavily on specialized terminology that may exclude non-specialist readers, particularly those from general machine learning backgrounds rather than robotics or probabilistic modeling.

In **Section 3.1**, the text states, "We model robot-environment interaction as a POMDP." The acronym **POMDP** is not defined here. While standard in reinforcement learning, it should be spelled out as "Partially Observable Markov Decision Process" upon first use to ensure accessibility. Similarly, the phrase "marginalize over all configurations" uses statistical jargon that could be simplified to "average over all configurations" for broader clarity.

In **Section 4.1**, the authors refer to "6 unseen OOD viewpoints." The acronym **OOD** (Out-of-Domain) is not defined until **Appendix A.1**. Acronyms should be defined at their first occurrence in the main text, not deferred to the appendix. This forces readers to flip pages to understand basic experimental setup terminology.

**Section 4.4** mentions reducing inference cost via "KV caching." This refers to **Key-Value caching**, a specific optimization technique in Transformer inference. While common in LLM literature, it is implementation-specific jargon that should be expanded for a general robotics audience.

The **Appendix A.1** proof relies on terms like "**d-separation**" and "**collider**." These are specific concepts from probabilistic graphical models. While mathematically precise, they create a barrier for readers who may not have a background in graphical models. A brief parenthetical explanation (e.g., "d-separation (a criterion for conditional independence)") would significantly improve readability without sacrificing rigor.

Finally, **Section 3.1** uses the term "**action chunk**." While common in imitation learning, "sequence of actions" is more universally understood. Additionally, **Appendix A.2** uses "**6-DoF**" without defining "Degrees of Freedom."

Addressing these points will make the paper more inclusive without diluting its technical contributions.
