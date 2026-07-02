---
action_items:
- id: 0a4dc21d4c03
  severity: writing
  text: Define 'VLA' and 'VLM' at first use in the Abstract. Currently, 'VLA' appears
    in the first sentence and 'VLM' in the second without prior definition, which
    excludes non-specialist readers.
- id: 6dcd38f6b49b
  severity: writing
  text: Replace the acronym 'SR' with 'Soft Success Rate' or 'success rate' in Section
    5.1. The text defines 'Soft Success Rate (SR)' but then immediately uses 'SR'
    in equations and subsequent text without re-stating the full term, creating a
    barrier for readers unfamiliar with the specific metric notation.
- id: b75a2c579e55
  severity: writing
  text: Define 'Action Expert' in Section 5.2. The term is introduced as 'VLM and
    Action Expert parts' without explaining what an 'Action Expert' is (e.g., a specific
    head, a separate network, or a module). This is internal jargon that needs a plain-English
    explanation.
- id: ebc205115b69
  severity: writing
  text: Replace 'backbone' with 'underlying neural network' or 'base model' in Section
    5.2 and throughout. While common in ML, 'backbone' is jargon that may confuse
    readers from other fields. Similarly, define 'probe' in the context of 'linear
    probe' (e.g., 'a simple linear classifier trained to...').
- id: 48070ed2a4e3
  severity: writing
  text: Define 'SFT' and 'RL' in Section 6.2. The text mentions 'fine-tune the model
    with both SFT and RL' without defining these acronyms (Supervised Fine-Tuning
    and Reinforcement Learning). These are standard but should be defined for a general
    audience.
artifact_hash: b7bf68dc7049e64af55a4f743a5addf0de48270ccdf470df63d9da46224951a5
artifact_path: projects/PROJ-848-does-vla-even-know-the-basics-measuring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:34:19.107018Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on field-specific acronyms and jargon that are not consistently defined for a general audience, potentially excluding non-specialist readers.

First, the abstract introduces "VLA" (Vision-Language-Action) and "VLM" (Vision-Language Model) without defining them. While standard in robotics/AI, a general reader needs these spelled out immediately. The same applies to "SFT" and "RL" in Section 6.2; these acronyms appear without definition.

Second, the term "Action Expert" is used in Section 5.2 ("VLM and Action Expert parts") without explanation. It is unclear if this refers to a specific architectural component, a head, or a module. This internal terminology should be clarified (e.g., "the action-prediction head").

Third, the metric "Soft Success Rate" is abbreviated as "SR" in Section 5.1. While the full name is given once, the subsequent heavy use of "SR" in equations and text assumes the reader has memorized the abbreviation. It would be clearer to use the full term or a more descriptive variable name in the text.

Finally, terms like "backbone" (used frequently to refer to the base model) and "probe" (in "linear probe") are standard ML jargon. While acceptable in a specialized venue, the paper claims to address "commonsense" and "world knowledge," suggesting a broader relevance. Replacing "backbone" with "base model" and explicitly defining "linear probe" as "a simple linear classifier trained on..." would improve accessibility without sacrificing precision.
