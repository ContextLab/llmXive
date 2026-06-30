---
action_items:
- id: 0cc04fe50c43
  severity: writing
  text: The paper relies heavily on domain-specific jargon from both journalism and
    AI engineering, which creates a barrier for the intended non-expert audience.
    In the Abstract, terms like "Computer-use agent" and "Inspector" are introduced
    as proper nouns without definition. A general reader needs to know immediately
    that an "Inspector" is a tool that links claims to sources, and that a "Computer-use
    agent" is an AI that navigates websites like a human. Section 1 introduces "angle
    coverage" without de
artifact_hash: c961c4f131b3e6127c44320a12751b53bf58ee9a86ae78d22dc551848222c6a2
artifact_path: projects/PROJ-719-data-journalist-agent-transforming-data/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T06:49:54.161438Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper relies heavily on domain-specific jargon from both journalism and AI engineering, which creates a barrier for the intended non-expert audience. 

In the **Abstract**, terms like "Computer-use agent" and "Inspector" are introduced as proper nouns without definition. A general reader needs to know immediately that an "Inspector" is a tool that links claims to sources, and that a "Computer-use agent" is an AI that navigates websites like a human. 

**Section 1** introduces "angle coverage" without defining "angle" in this context; "perspective overlap" would be clearer. The term "lede" in Section 3 is specific journalism slang for the opening sentence and should be replaced with "opening" or "lead." 

In **Section 3**, the authors use the colloquialism "slop" to describe low-quality LLM content. This is informal and potentially confusing; "automated low-quality content" is more precise. Additionally, "cross-family" is used to describe the verifier agent, a term that assumes knowledge of agent architecture families. 

**Section 5** uses "scrollytelling" to describe a specific style of interactive web design. This is industry jargon that should be expanded to "scroll-triggered storytelling" or "interactive scrolling narrative" for clarity. The acronym "NOC" appears in the analysis of Olympic data without being spelled out (National Olympic Committee). 

Finally, the term "grounded" is used frequently (e.g., "evidence-grounded") but is a technical AI term. While the paper explains the mechanism, the adjective itself should be briefly contextualized for readers unfamiliar with "grounding" in LLMs. Replacing these terms with plain language will significantly improve accessibility without sacrificing precision.
