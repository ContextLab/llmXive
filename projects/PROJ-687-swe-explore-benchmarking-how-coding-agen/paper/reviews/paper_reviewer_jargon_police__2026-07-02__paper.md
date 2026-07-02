---
action_items:
- id: 7401071ad6ab
  severity: writing
  text: Define 'agentic explorers' and 'agentic localization' upon first use. The
    term 'agentic' is used as a noun/adjective without definition, assuming reader
    familiarity with specific agent architectures.
- id: a226c048257a
  severity: writing
  text: Define 'trajectory-grounded' and 'trajectory-grounded supervision' at first
    mention. While context implies it relates to agent execution logs, the specific
    mechanism of deriving ground truth from trajectories needs a plain-language gloss.
- id: 1b2924848ada
  severity: writing
  text: Replace 'downstream repair behavior' with 'subsequent code-fixing performance'
    or similar. 'Downstream' is standard in ML but can be opaque to general software
    engineering readers; 'repair behavior' is slightly jargon-heavy compared to 'fixing
    bugs'.
- id: 26609fc08b2a
  severity: writing
  text: Define 'restricted-context environment' or 'restricted-context validation'
    clearly. The term implies a specific experimental setup but lacks a brief explanatory
    clause for non-specialists.
- id: 378f2499ca2e
  severity: writing
  text: Clarify 'operating point' in Section 5.2. The phrase 'occupy nearly the same
    operating point' is technical jargon from systems/ML that should be replaced with
    'perform similarly' or 'achieve comparable results' for broader accessibility.
artifact_hash: d01bf725e90093797f2151085112b0bd34f0dac442648b3b22aae07b0ee791b3
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:45:47.449096Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized terminology that assumes a high degree of familiarity with the current landscape of LLM-based software engineering agents. While the target audience is likely researchers in this specific sub-field, several terms are used without definition, potentially excluding readers from adjacent fields (e.g., traditional software engineering or general NLP).

First, the term **"agentic"** is used repeatedly as both an adjective and a noun (e.g., "agentic explorers," "agentic localization," "agentic behavior") without a definition. It is unclear if this refers to any system with an LLM, systems with tool-use capabilities, or a specific architectural pattern. A brief clarification or replacement with "agent-based" or "autonomous" would improve clarity.

Second, **"trajectory-grounded"** and **"trajectory-grounded supervision"** are central to the paper's methodology but are not explicitly defined in plain language. The text assumes the reader understands that this means deriving labels from the sequence of actions taken by a successful agent. A phrase like "ground truth derived from the step-by-step actions of successful agents" would be more accessible.

Third, the phrase **"downstream repair behavior"** appears frequently. While "downstream" is common in ML pipelines, "repair behavior" is slightly jargon-heavy. Replacing this with "subsequent code-fixing performance" or "ability to fix the bug" would be more direct. Similarly, **"restricted-context environment"** is used to describe the validation protocol but lacks a brief explanatory clause for what "restricted" entails (i.e., hiding parts of the codebase).

Finally, the term **"operating point"** in Section 5.2 ("occupy nearly the same operating point") is technical jargon. Replacing this with "perform similarly" or "achieve comparable results" would make the finding clearer to a broader audience.

These changes are minor but necessary to ensure the paper's contributions are accessible to the wider software engineering community, not just those deeply embedded in the current "agent" literature.
