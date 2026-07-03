---
action_items:
- id: 5e9904d095ab
  severity: science
  text: The manuscript suffers from significant jargon overuse, particularly in the
    introduction and the "Open Problems" sections, where the authors coin or repurpose
    terms without sufficient definition for a general audience. The central term "harness"
    is used as a proper noun ("Code as Agent Harness") throughout, yet the text never
    explicitly defines it as the "runtime infrastructure and execution environment"
    distinct from the model itself. This forces the reader to infer the meaning from
    context, wh
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:41:26.270615Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The manuscript suffers from significant jargon overuse, particularly in the introduction and the "Open Problems" sections, where the authors coin or repurpose terms without sufficient definition for a general audience. The central term "harness" is used as a proper noun ("Code as Agent Harness") throughout, yet the text never explicitly defines it as the "runtime infrastructure and execution environment" distinct from the model itself. This forces the reader to infer the meaning from context, which is a barrier to entry.

Specific instances of undefined or opaque terminology include "organicity" (Section 5.1.1), which appears to be a neologism for "adherence to project conventions" but is presented as a standard metric. Similarly, "cybernetic governor" (Section 3.4) uses historical control theory jargon where "safety governor" or "control mechanism" would be clearer. Acronyms such as "PEV" (Plan-Execute-Verify), "AHE" (Agentic Harness Engineering), "MCP" (Model Context Protocol), and "HITL" (Human-in-the-Loop) are introduced without explicit expansion at their first occurrence in the main text, violating standard readability practices.

The text frequently relies on dense, abstract phrasing like "latent state," "semantic conflict resolution," and "epistemic weight" without grounding these in plain English explanations. For instance, the discussion of "belief-state divergence" ($|B_k - S_k|$) in Section 4.1 assumes the reader understands the specific formalism of belief states in multi-agent systems without a brief, intuitive explanation. The paper needs a dedicated glossary or a more rigorous "Definition" section early on to establish the vocabulary, and a systematic pass to replace coined terms with standard, descriptive language.
